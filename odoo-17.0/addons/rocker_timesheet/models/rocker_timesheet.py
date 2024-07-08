# -*- coding: utf-8 -*-
#############################################################################
#
#    Copyright (C) 2021-Antti Kärki.
#    Author: Antti Kärki.
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models, _
#from odoo.exceptions import UserError, AccessError, Warning
from odoo.exceptions import UserError, AccessError
from odoo import tools
from datetime import timedelta, datetime, date, time, timezone
from dateutil.rrule import rrule, DAILY
from odoo.osv import expression
import pytz

import logging

_logger = logging.getLogger(__name__)
# Default star/stop/amount/duration if compny or user default are not set
# set values to be created in _get_defaults method
default_start_time = 9
default_end_time = 17.0
default_duration = 8.0  # contains lunch hours
default_unit_amount = 7.5  # lunch not paid
default_rolling_amount = 1
default_time_roundup = -1

project_change = True
user_values = [(0, 0, 'filter', False)]         # this is like cookie pool or user context because I can not use those
daystocreate = 0
prev_company = -1

# btw....remember to check odoo global defaults....working day, is it 8 or 7.5 hours...has to be in sync with rocker company / user defaults

class RockerTimesheet(models.Model):
    _inherit = 'account.analytic.line'
    _name = 'account.analytic.line'
    _order = "start desc"

    @api.model
    def _default_user(self):
        _logger.debug('_default_user')
        return self.env.context.get('user_id', self.env.user.id)

    def _domain_project_id(self):
        domain = [('allow_timesheets', '=', True)]
        return expression.AND([domain,
                               ['|', ('privacy_visibility', '!=', 'followers'), ('message_partner_ids', 'in', [self.env.user.partner_id.id])]
                               ])

    def _domain_project_id_search(self):
        domain = ['|',('company_id', '=', self.env.company.id),('company_id', '=', '')]
        return domain

    def _set_rolling(self, bset):
        _logger.debug('Setting rolling true')
        _i = 0
        _bfound = False
        _i = int(self.env.user.id)
        for i in range(len(user_values)):
            if user_values[i][0] == _i:
                user_values[i][3] = bset
                _bfound = True
        if not _bfound:
            values1 = [_i, 0, '', False]
            user_values.append(values1)
        return True

    def _get_rolling(self):
        _i = 0
        _brolling = False
        _bfound = False
        _i = int(self.env.user.id)
        for i in range(len(user_values)):
            if user_values[i][0] == _i:
                _brolling = user_values[i][3]
                _bfound = True
        if not _bfound:
            _logger.debug('Rolling factor not found')
            return False
        _logger.debug('Rolling Factor: ' + str(_brolling))
        return _brolling

    def _set_search_id(self, id):
        _logger.debug('Setting search Id: ' + str(id))
        _i = 0
        _bfound = False
        _i = int(self.env.user.id)
        for i in range(len(user_values)):
            if user_values[i][0] == _i:
                user_values[i][1] = id  # selected task_id
                _bfound = True
        if not _bfound:
            values1 = [_i, id, '', False]
            user_values.append(values1)
        return True

    def _get_search_id(self):
        _i = 0
        _selected_id = 0
        _bfound = False
        _i = int(self.env.user.id)
        for i in range(len(user_values)):
            if user_values[i][0] == _i:
                _selected_id = user_values[i][1]
                _bfound = True
        if not _bfound:
            _logger.debug('Selected id not found')
            return -1
        _logger.debug('Searchpanel selected id: ' + str(_selected_id))
        return _selected_id

    def _domain_get_search_filter(self):
        _i = 0
        _filt = ""
        _bfound = False
        _i = int(self.env.user.id)
        for i in range(len(user_values)):
            if user_values[i][0] == _i:
                _filt = user_values[i][2]
                _bfound = True
        if not _bfound:
            _logger.debug('filter not found')
            return ""
        _logger.debug('Returning _search_panel_filter: ' + str(_filt))
        return _filt

    def _domain_set_search_filter(self, filt):
        _i = 0
        _bfound = False
        _i = int(self.env.user.id)
        for i in range(len(user_values)):
            if user_values[i][0] == _i:
                user_values[i][2] = filt
                _bfound = True
        if not _bfound:
            values1 = [_i, 0, filt, False]
            user_values.append(values1)
        return True

    def _domain_get_search_domain(self, filt):
        # default = all
        _search_panel_domain = ['|',('company_id', '=', self.env.company.id),('company_id', '=', False)]  # ok
        if filt == 'all':
            _search_panel_domain = _search_panel_domain + []
        elif filt == 'member':
            _search_panel_domain = _search_panel_domain + [('project_id', 'in', self.env['project.project'].search([('message_partner_ids', 'in', [self.env.user.partner_id.id])]).ids)]
        elif filt == 'internal':
            _search_panel_domain = _search_panel_domain + [
                ('project_id', 'in', self.env['project.project'].search([('rocker_type', '=', 'internal')]).ids)]
        elif filt == 'billable':
            _search_panel_domain = _search_panel_domain + [
                ('project_id', 'in', self.env['project.project'].search([('rocker_type', '=', 'billable')]).ids)]
        elif filt == 'nonbillable':
            _search_panel_domain = _search_panel_domain + [
                ('project_id', 'in', self.env['project.project'].search([('rocker_type', '=', 'nonbillable')]).ids)]
        elif filt == 'mine':
            _search_panel_domain = _search_panel_domain + \
                                   ['|',
                                    ('task_id', 'in', self.env['rocker.task'].search([('user_id', '=', self.env.user.id)]).ids),
                                    '&',  ('task_id', '=', False),
                                    ('project_id', 'in', self.env['rocker.task'].search([('user_id', '=', self.env.user.id)]).project_id.ids),
                                    ]

        else:
            self._domain_get_search_domain('all')
        _search_panel_domain = expression.AND([_search_panel_domain,
                                               ['|', ('privacy_visibility', '!=', 'followers'), ('project_id.message_partner_ids', 'in', [self.env.user.partner_id.id])]
                                               ])
        return _search_panel_domain

    def _get_defaults(self):
        _logger.debug('_get_defaults')
        global default_start_time
        global default_end_time
        global default_duration
        global default_unit_amount
        global default_rolling_amount
        global default_time_roundup

        _defaults = None
        _company_defaults = None
        _company_defaults = self.env['rocker.company.defaults'].search([('company_id', '=', self.env.company.id)])
        _defaults = self.env['rocker.user.defaults'].search(
            [('user_id', '=', self.env.user.id), ('company_id', '=', self.env.company.id)]) \
                    or self.env['rocker.company.defaults'].search([('company_id', '=', self.env.company.id)])
        if _defaults:

            default_start_time = _defaults.rocker_default_start or _company_defaults.rocker_default_start
            default_end_time = _defaults.rocker_default_stop or _company_defaults.rocker_default_stop
            default_duration = (_defaults.rocker_default_stop - _defaults.rocker_default_start) or (_company_defaults.rocker_default_stop - _company_defaults.rocker_default_start)
            default_unit_amount = _defaults.rocker_default_work or _company_defaults.rocker_default_work or 7.5
            default_rolling_amount = _defaults.rocker_default_rolling_work or _company_defaults.rocker_default_rolling_work or 1
            default_time_roundup = int(_defaults.rocker_round_up) or int(_company_defaults.rocker_round_up) or 0
        else:
            _logger.debug('No defaults, creating company defaults')
            _start = self.to_UTC(9)
            _end = self.to_UTC(17)
            self.env['rocker.company.defaults'].sudo().create({
                'company_id': self.env.company.id,
                'rocker_default_start': _start,
                'rocker_default_stop': _end,
                'rocker_default_work': 7.5,
                'rocker_round_up': '0',
                'rocker_default_rolling_work': 1
            })
            self._get_defaults()
        return True

    def _default_start(self):
        _logger.debug('_set_default_start')
        # this one can not be used, if row created from hr_timesheet or hr_leave then it sets rocker defaults
        return

    def _default_date(self):
        _logger.debug('_set_default_date')
        # this one can not be used, if row created from hr_timesheet or hr_leave then it sets rocker defaults
        return

    def _default_stop(self):
        _logger.debug('_set_default_stop')
        # this one can not be used, if row created from hr_timesheet or hr_leave then it sets rocker defaults
        return

    def _default_duration(self):
        _logger.debug('_set_default_duration')
        # this one can not be used, if row created from hr_timesheet or hr_leave then it sets rocker defaults
        return

    def _default_work(self):
        _logger.debug('_set_default_work')
        # this one can not be used, if row created from hr_timesheet or hr_leave then it sets rocker defaults
        return

    def _calculate_duration(self, start, stop):
        _logger.debug('_calculate_duration')
        if not start or not stop:
            return 0
        duration = (stop - start).total_seconds() / 3600
        return round(duration, 2)

    def _default_name(self):
        _logger.debug('_default_name')
        _selected_id = 0
        _selected_id = self._get_search_id()
        if _selected_id > 0:
            search_task = self.env['project.task'].search([('id', '=', _selected_id)], limit=1)
            if search_task.id > 0:
                _logger.debug('_default_name: ' + str(search_task.name) + ': ')
                return str(search_task.name) + ': '
        else:
            return None

    def _default_task(self):
        _logger.debug('_default_task')
        _selected_id = 0
        _selected_id = self._get_search_id()
        if _selected_id > 0:
            _logger.debug('_default_task selected id')
            search_task = self.env['project.task'].search([('id', '=', _selected_id)], limit=1)
            if search_task.id > 0:
                _logger.debug('_default task return task id id')
                return search_task.id
        _logger.debug('return none')
        return None

    def _default_project(self):
        _logger.debug('_default_project')
        _selected_id = 0
        _selected_id = self._get_search_id()
        if _selected_id > 0:
            search_task = self.env['project.task'].search([('id', '=', _selected_id)], limit=1)
            if search_task.id > 0:
                _logger.debug('_default project return project id')
                return search_task.project_id
        _logger.debug('_default project return none')
        return None

    # existing fields
    company_id = fields.Many2one('res.company', "Company", default=lambda self: self.env.company, store=True,
                                 required=True)
    project_id = fields.Many2one(
        'project.project', 'Project', compute='_compute_project_id', store=True, readonly=False,
        domain=_domain_project_id)
    task_id = fields.Many2one(
        'project.task', 'Task', compute='_compute_task_id', store=True, readonly=False, index=True,
        domain="[('company_id', '=', company_id), ('project_id.allow_timesheets', '=', True), ('project_id', '=?', project_id)]")
    name = fields.Char(required=False, default=_default_name)

    # new fields
    display_name = fields.Char('Description', required=False, store=False, compute='_compute_display_name')
    rocker_type = fields.Selection([
        ('internal', 'Internal'),
        ('billable', 'Billable'),
        ('nonbillable', 'Non Billable'),
        ('time_off', 'Time Off'),
    ], 'Project Type', required=False, default='', store=False,
        related='project_id.rocker_type', compute='_compute_rocker_type')
    task_search = fields.Many2one(
        'rocker.task', 'Project', store=True, readonly=False, required=False)
    rocker_search_type = fields.Selection([
        ('all', 'All'),
        ('mine', 'My Tasks'),
        ('billable', 'Billable'),
        ('nonbillable', 'Non Billable')], 'Search Type', store=False, required=False, default='all')
    # required fields
    # changed to non required, we handle this in views, (otherwise old timesheet app does not work)
    start = fields.Datetime(
        'Start', required=False, readonly=False, default=_default_start, store=True,
        help="Start datetime of a task")
    stop = fields.Datetime(
        'Stop', required=False, readonly=False, default=_default_stop, store=True,
        help="Stop datetime of a task")
    allday = fields.Boolean('All Day', default=False, required=False)  # required in order calendar to work
    #
    daystocreateshow = fields.Integer('Generate', required=False, readonly=True, store=False,
                                      help="Create number of timeheet rows")
    duration = fields.Float('Duration', store=True, readonly=False, default=_default_duration, required=True, help="Work duration in hours")

    # existing fields
    date = fields.Date('Date', required=True, index=True, store=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, required=True)
    employee_id = fields.Many2one('hr.employee', "Employee",
                                  default=lambda self: self.env['hr.employee'].search(
                                      [('user_id', '=', self.env.user.id),
                                       ('company_id', '=', self.env.company.id)]).id, store=True)
    department_id = fields.Many2one('hr.department', "Department", compute='_compute_department_id', store=True,
                                    compute_sudo=True)
    unit_amount = fields.Float('Actual Work', default=_default_work, required=True, help="Work amount in hours")

    # def init(self):
    #     # when module is installed or upgraded
    #     _logger.debug('init')

    # def __init__(self, pool, cr):
    #     # when server starts or restarted
    #     _logger.debug('Rocker: __init__')
    #     return super().__init__(pool, cr)

    @api.depends('project_id')
    def _compute_project_id(self):
        _logger.debug('api depends project id')
        if not self.project_id and self._get_search_id() > 0:
            search_task = self.env['project.task'].search([('id', '=', self._get_search_id())], limit=1)
            _logger.debug('search_task')
            _logger.debug(search_task)
            if not search_task.id:
                _logger.debug('Project not found from project.task...')
                return False
            #
            _logger.debug('search project id: ' + str(search_task.project_id.id))
            for line in self:
                self.project_id = search_task.project_id.id
                self.task_id = search_task.id
        elif self.task_id:
            self.project_id = self.task_id.project_id


    @api.depends('task_id')
    def _compute_task_id(self):
        _logger.debug('_compute task id')
        if not self.task_id and self._get_search_id() > 0:
            search_task = self.env['project.task'].search([('id', '=', self._get_search_id())], limit=1)
            _logger.debug(search_task)
            if not search_task.id:
                _logger.debug('Task not found from project.task...')
                return False
            _logger.debug('search task id: ' + str(search_task.id))
            for line in self:
                self.task_id = search_task.id

    @api.depends('name','unit_amount')
    def _compute_display_name(self):
        _logger.debug('api depends name, unit_amount')
        for line in self:
            line.display_name = "%s %s %s %s %0.1f %s" % (line.task_id.name , ': ' , line.name, ' - ', line.unit_amount or 0, ' h')

    @api.depends('user_id')
    def _compute_employee_id(self):
        _logger.debug('api depends user_id')
        for line in self.filtered(lambda line: not line.employee_id):
            line.employee_id = line.user_id.employee_id

    @api.depends('department_id')
    def _compute_department_id(self):
        _logger.debug('api depends department_id')
        for line in self:
            line.department_id = line.employee_id.department_id or line.user_id.employee_id.department_id  # single or multi company

    @api.depends('company_id')
    def _compute_company_id(self):
        _logger.debug('api depends company_id')
        for line in self:
            line.company_id = line.employee_id.company_id


    #############################
    # read search create unlink
    #############################

    @api.model
    def create(self, vals):
        global default_start_time
        global default_end_time
        global default_duration
        global default_unit_amount
        global default_rolling_amount
        global default_time_roundup
        self._get_defaults()
        # creation from hr_timesheet or time_off: set stop & duration
        if 'date' in vals and not 'start' in vals:
            _logger.debug('Creation comes somewhere else than Rocker')
            global default_start_time
            global default_end_time
            global default_duration
            global default_unit_amount
            global default_rolling_amount
            global default_time_roundup
            self._get_defaults()
            _logger.debug(vals['date'])
            if 'holiday_id' in vals and vals.get('holiday_id'):
                _logger.debug('Creation comes from time_off')
                _logger.debug('Holiday id: ' + str(vals['holiday_id']))
                time_off = self.env['hr.leave'].search([('id', '=', vals['holiday_id'])])
                _logger.debug('Hour from: ' + str(time_off.request_hour_from))
                if time_off.request_hour_from != False:
                    _logger.debug(time_off.date_from)
                    vals['start'] = (time_off.date_from).strftime('%Y-%m-%d %H:%M')
                    vals['stop'] = (time_off.date_to).strftime('%Y-%m-%d %H:%M')
                    vals['duration'] = vals['unit_amount']
                    vals['allday'] = False
                else:
                    _logger.debug(vals['date'])
                    vals['start'] = (fields.Datetime.from_string(vals['date']) + timedelta(hours=default_start_time)).strftime('%Y-%m-%d %H:%M')
                    vals['stop'] = (fields.Datetime.from_string(vals['start']) + timedelta(hours=float(vals['unit_amount']))).strftime('%Y-%m-%d %H:%M')
                    vals['duration'] = vals['unit_amount']
                    if float(vals['unit_amount']) >= default_unit_amount:
                        # I don't like this...better to show all in weekly calendar as timeslots
                        # btw....remember to check odoo global defaults....working day is it 8 or 7.5 hours
                        # vals['allday'] = True
                        vals['allday'] = False
                    else:
                        vals['allday'] = False

            else:   # can not tell if it comes from sales tiimesheet or just hr_timesheet but who cares
                _logger.debug('Creation comes from hr_timesheet')
                vals['start'] = (fields.Datetime.from_string(vals['date']) + timedelta(hours=default_start_time)).strftime('%Y-%m-%d %H:%M')
                vals['stop'] = (fields.Datetime.from_string(vals['start']) + timedelta(hours=float(vals['unit_amount']))).strftime('%Y-%m-%d %H:%M')
                vals['duration'] = vals['unit_amount']
                vals['allday'] = False
            _logger.debug('Values:')
            _logger.debug(vals)


            record = super(RockerTimesheet, self).create(vals)
            return record
        # Rocker specific data
        _logger.debug('Rocker create used')
        _logger.debug('Values:')
        _logger.debug(vals)
        _brolling = self._get_rolling()

        #
        if 'date' not in vals:
            vals['date'] = fields.Datetime.from_string(vals['start']).date()
        # date field is invisible on Rocker timesheet tree view, it is not set
        if 'date' in vals and not vals.get('date'):
            vals['date'] = fields.Datetime.from_string(vals['start']).date()
        _selected_id = -1
        if vals.get('task_id') == False:
            _logger.debug('Task selected from searchpanel')
            _selected_id = self._get_search_id()
            if _selected_id > 0:
                _logger.debug('Selected id set, search task...')
                search_task = self.env['project.task'].search([('id', '=', _selected_id)], limit=1)
                if not search_task.id:
                    _logger.debug('Task not found from project.task...')
                    return False
                vals['task_id'] = search_task.id
                vals['project_id'] = search_task.project_id.id
            else:
                raise UserError(_('Select Project & Task from drop-down fields'))
        if vals['name'] == False:
            if vals.get('task_id'):
                _name = self.env['project.task'].browse(vals['task_id']).name
            if _name:
                vals['name'] = _name

        # project implies analytic account
        if not vals.get('account_id'):
            _logger.debug('Account_id missing...')
            # if imported from Excel, then there is no project_id
            task = self.env['project.task'].browse(vals.get('task_id'))
            project = self.env['project.project'].search([('id', '=', task.project_id.id)], limit=1)
            _logger.debug('Added account_id: ' + str(project.analytic_account_id))
            vals['account_id'] = project.analytic_account_id.id

        # CREATE first row
        _logger.debug('Insert date ' + str(vals['date']))
        _logger.debug('Insert start date: '    + str(vals['start']))
        _logger.debug('Insert stop date: ' + str(vals['stop']))

        # If stop date > start date --> change stop (we create one row per day)
        if fields.Datetime.from_string(vals['stop']).date() > fields.Datetime.from_string(vals['start']).date():
            _logger.debug('Changing stop date ')
            _logger.debug('Stop time: ' + fields.Datetime.from_string(vals['stop']).time().strftime('%H:%M'))
            vals['stop'] = (datetime.combine(fields.Datetime.from_string(vals['start']).date(),
                            fields.Datetime.from_string(vals['stop']).time())).strftime('%Y-%m-%d %H:%M')
            vals['duration'] = str(self._calculate_duration(fields.Datetime.from_string(vals['start']), fields.Datetime.from_string(vals['stop'])))

        record = super(RockerTimesheet, self).create(vals)
        # row created, should we create more
        global daystocreate
        if daystocreate > 0:
            i = 0
            while i < daystocreate:
                _logger.debug('Create more ' + str(i))
                vals['date'] = fields.Datetime.from_string(vals['date']) + timedelta(days=1)
                vals['start'] = fields.Datetime.from_string(vals['start']) + timedelta(days=1)
                vals['stop'] = fields.Datetime.from_string(vals['stop']) + timedelta(days=1)
                _logger.debug('Inserting date ' + str(vals['date']))
                _logger.debug('Inserting start ' + str(vals['start']))
                _logger.debug('Inserting stop ' + str(vals['stop']))
                record = super(RockerTimesheet, self).create(vals)
                i += 1
        self._set_rolling(False)  # default is Create button with default starty & Stop, Rolling is set is Rolling button clicked
        return record

    def write(self, vals):
        _logger.debug('Write')
        _logger.debug(self.holiday_id)
        # calendar changes duration if moved/sized but not unit_amount/work
        if 'duration' in vals and not vals.get('unit_amount'):
            _logger.debug('changing unit_amount')
            vals['unit_amount'] = vals['duration']

        if 'date' in vals and not 'start' in vals:
            result = super(RockerTimesheet, self).write(vals)
            return result
        else:
            _logger.debug('Rocker write used')

        if 'holiday_id' in self.env['account.analytic.line']._fields:
            if self.holiday_id and 'start' in vals:
                _logger.debug('Time Off module in use')
                raise UserError(_('Edit row in Time off module!'))
                return False

        if vals.get('duration'):
            if vals['duration'] > 24:
                raise UserError(_('One timesheet row per day...duration can not exceed 24'))
        result = super(RockerTimesheet, self).write(vals)
        return result

    # ----------------------------------------------------------
    # SearchPanel
    # ----------------------------------------------------------

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        _logger.debug('Search_read...')
        _logger.debug('domain: ' + str(domain))
        _logger.debug('fields: ' + str(fields))
        # args = args + self._domain_project_id_search()
        clause = []
        # # selected_id = 0
        i = 0
        for clause in domain:
            _logger.debug('clause: ' + str(clause))
            if clause[0] == 'task_search':
                # selected_id = int(clause[2])
                if int(clause[2]) > 0:  # id > 0 when task, project row has < 1
                    self._set_search_id(int(clause[2]))
                    _logger.debug('Selected id set to: ' + str(self._get_search_id()))
                else:
                    self._set_search_id(0)
                clause[0] = 'task_search'
                clause[1] = '<>'
                clause[2] = ' '
            i += 1
        _logger.debug('domain: ' + str(domain))
        # domain = []  # return all rows to calendar
        records = super(RockerTimesheet, self).search_read(domain, fields, offset, limit, order)
        return records

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        if field_name != 'task_search':
            _logger.debug('Rocker search panel NOT used')
            return super(RockerTimesheet, self).search_panel_select_range(field_name, **kwargs)
        else:
            _logger.debug('Rocker search panel used')
        # rocker
        global prev_company
        _company_changed = False
        if prev_company != self.env.company.id:
            # we need to refresh searchpanel,someone changed company :-)
            prev_company = self.env.company.id
            _company_changed = True
            self._domain_set_search_filter('all')
        if field_name == 'task_search':
            if self._domain_get_search_filter() == "":
                self._domain_set_search_filter('all')
            search_domain = self._domain_get_search_domain(self._domain_get_search_filter())
            # this works in Odoo 14
            return super(RockerTimesheet, self).search_panel_select_range(
                field_name, comodel_domain=search_domain, **kwargs
            )

        return super(RockerTimesheet, self).search_panel_select_range(field_name, **kwargs)

    def create_rolling(self):
        _logger.debug('Create rolling item...')
        self._set_rolling(True)
        return

    def searchpanel_all(self, filt):        # called from javascript
        _logger.debug('Searchpanel_all...' + filt)
        if filt == 'all':
            self._domain_set_search_filter('all')
        elif filt == 'member':
            self._domain_set_search_filter('member')
        elif filt == 'billable':
            self._domain_set_search_filter('billable')
        elif filt == 'nonbillable':
            self._domain_set_search_filter('nonbillable')
        elif filt == 'internal':
            self._domain_set_search_filter('internal')
        elif filt == 'mine':
            self._domain_set_search_filter('mine')
        else:
            self._domain_set_search_filter('all')
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
        # return


    @api.model
    def get_unusual_days(self, date_from, date_to=None):
        # Checking the calendar directly allows to not grey out the leaves taken
        # by the employee
        calendar = self.env.user.employee_id.resource_calendar_id
        if not calendar:
            return {}
        tz = pytz.timezone('UTC')
        usertime = pytz.utc.localize(datetime.now()).astimezone(tz)
        dfrom = pytz.utc.localize(datetime.combine(fields.Date.from_string(date_from), time.min)).astimezone(tz)
        dto = pytz.utc.localize(datetime.combine(fields.Date.from_string(date_to), time.max)).astimezone(tz)

        works = {d[0].date() for d in calendar._work_intervals_batch(dfrom, dto)[False]}
        return {fields.Date.to_string(day.date()): (day.date() not in works) for day in rrule(DAILY, dfrom, until=dto)}

    # ----------------------------------------------------------
    # On Change
    # ----------------------------------------------------------

    @api.onchange('duration')
    def _onchange_duration(self):
        _logger.debug('_onchange_duration')
        if self.duration and self.start and self.unit_amount:
            self.duration = self.rocker_round_up(self.duration) # do not change unit_amount, duration can be longer
            self.stop = fields.Datetime.from_string(self.start) + timedelta(hours=self.duration)
            if self._calculate_duration(self.start,self.stop) < self.unit_amount:
                self.stop = (fields.Datetime.from_string(self.start) + timedelta(hours=self.unit_amount)).strftime('%Y-%m-%d %H:%M')
                self.duration = self.rocker_round_up(self.unit_amount)
                raise UserError(_('Duration is less than Work Amount!'))
                return False
        if self.duration > 0 and not self.unit_amount:
            global default_unit_amount
            self._get_defaults()
            self.unit_amount = default_unit_amount

    @api.onchange('start')
    def _onchange_start(self):
        _logger.debug('_onchange_start')
        if 'holiday_id' in self.env['account.analytic.line']._fields:
            if self.holiday_id:
                _logger.debug('Time Off module in use')
                raise UserError(_('Edit row in Time off module!'))
                return False

        global default_start_time
        global default_end_time
        global default_duration
        global default_unit_amount
        global default_rolling_amount
        global default_time_roundup

        self._get_defaults()

        if not self.start:
            _broll = None
            _broll = self._get_rolling()
            if _broll == True:  # set start date = max stop
                _logger.debug('Rolling start...')
                query = 'SELECT MAX(stop) as max_stop FROM account_analytic_line where user_id = ' + str(self.env.user.id) + \
                        ' and company_id = ' + str(self.env.company.id)
                self.env.cr.execute(query)
                max_stop = None
                max_stop = self.env.cr.fetchone()
                if max_stop[0]:
                    self.start =  max_stop[0].strftime('%Y-%m-%d %H:%M')
                else:
                    return False
            else:
                _now = fields.Date.today().strftime('%Y-%m-%d %H:%M')
                self.start = (fields.Datetime.from_string(_now) + timedelta(hours=default_start_time)).strftime('%Y-%m-%d %H:%M')


        global daystocreate
        daystocreate = 0
        _delta = 0
        _logger.debug('Start date: ' + str(self.start))
        _logger.debug('Stop date: ' + str(self.stop))
        if self.stop and self.start:
            _delta = self.stop.date() - self.start.date()
            daystocreate = _delta.days
            _logger.debug('Needs to create ' + str(daystocreate) + ' extra timesheet rows')

        self.date = self.start
        _logger.debug('Date: ' + str(self.date))

        self.allday = False

        if not self.stop: # real stop setting later has to have something
            self.stop = self.start
        #
        fmt = "%Y-%m-%d %H:%M"
        _logger.debug('Start date.time: ' + str(fields.Datetime.from_string(self.start).time()))
        _dt = fields.Datetime.from_string(self.start).time()
        if  (_dt.hour == 0 and _dt.minute == 0 and _dt.second == 0): # or self.stop.date() == self.start.date():
            self.daystocreateshow = daystocreate + 1
            # change to create only one day, create() then generates more days
            _date = fields.Datetime.from_string(self.start)
            self.start = (fields.Datetime.from_string(self.start.date()) + timedelta(hours=default_start_time)).strftime('%Y-%m-%d %H:%M')
            # we change this to one day, in create we create the rest
            self.stop = (fields.Datetime.from_string(self.stop.date()) + timedelta(hours=default_end_time)).strftime('%Y-%m-%d %H:%M')
            _logger.debug('Stop date.time: ' + str(fields.Datetime.from_string(self.stop).time()))
            self.duration = self._calculate_duration(self.start,self.stop)
            self.unit_amount = self._default_work()
        else:
            _broll = None
            _broll = self._get_rolling()
            self.date = fields.Datetime.from_string(self.start).date()
            if self.start == self.stop:    # stop was not set, we take defaults
                _amount = None
                if _broll:
                    self.stop = (fields.Datetime.from_string(self.start) + timedelta(hours=default_rolling_amount)).strftime('%Y-%m-%d %H:%M')
                    self.duration = self._calculate_duration(self.start, self.stop)
                    self.unit_amount = default_rolling_amount
                else:
                    self.stop = (fields.Datetime.from_string(self.start.date()) + timedelta(hours=default_end_time)).strftime('%Y-%m-%d %H:%M')
                    self.duration = self._calculate_duration(self.start, self.stop)
                    self.unit_amount = default_unit_amount
            else:
                self.duration = self._calculate_duration(self.start, self.stop)
                self.unit_amount = self.duration
            self.daystocreateshow = 0

    @api.onchange('unit_amount')
    def _onchange_unit_amount(self):
        _logger.debug('_onchange_unit_amount')
        if 'holiday_id' in self.env['account.analytic.line']._fields:
            if self.holiday_id:
                _logger.debug('Time Off module in use')
                raise UserError(_('Edit row in Time off module!'))
                return False

        if self.unit_amount and self.start:
            global default_start_time
            global default_end_time
            global default_duration
            global default_unit_amount
            global default_rolling_amount
            global default_time_roundup
            self._get_defaults()

            if self.unit_amount != default_unit_amount:     # do not change if defaults used (duration can be other than unit_amount
                self.unit_amount = self.rocker_round_up(self.unit_amount)
                self.stop = (fields.Datetime.from_string(self.start) + timedelta(hours=self.unit_amount)).strftime('%Y-%m-%d %H:%M')
                self.duration = self.rocker_round_up(self.unit_amount)

    @api.onchange('stop')
    def _onchange_stop(self):
        _logger.debug('_onchange_stop')
        if self.stop and self.start:
            if fields.Datetime.from_string(self.stop) < fields.Datetime.from_string(self.start):
                raise UserError(_('Stop before start!'))
            self.duration = self._calculate_duration(self.start,self.stop)

    def rocker_round_up(self, dt):
        global default_start_time
        global default_end_time
        global default_duration
        global default_unit_amount
        global default_rolling_amount
        global default_time_roundup
        self._get_defaults()
        if default_time_roundup > 0:
            _minutes = dt * 60
            _hours, _minutes = divmod(_minutes, 60)
            _approx = round(_minutes / default_time_roundup) * default_time_roundup
            _t = _hours + _approx / 60
            dt = _t
        return dt

    def to_UTC(self, dt):
        user = self.env.user
        if user.tz:
            tz = pytz.timezone(user.tz) or pytz.utc
            usertime = pytz.utc.localize(datetime.now()).astimezone(tz)
            offset = tz.utcoffset(datetime.now())
        else:
            tz = pytz.timezone('UTC')
            usertime = pytz.utc.localize(datetime.now()).astimezone(tz)
            offset = tz.utcoffset(datetime.now())

        return dt - offset.total_seconds() / 3600
