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
# from odoo.exceptions import UserError, AccessError, Warning
from odoo.exceptions import UserError, AccessError
from datetime import timedelta, datetime, date, time, timezone
import pytz

import logging

_logger = logging.getLogger(__name__)


class RockerCompany(models.Model):
    _name = 'rocker.company.defaults'
    _description = 'Rocker Company Defaults'
    _sql_constraints = [
        ('unique_defaults', 'unique (company_id)', 'Only one defaults per company!'),
        ('amount_positive', 'CHECK(rocker_default_work > 0)', 'Work must be positive'),
        ('rolling_work_positive', 'CHECK(rocker_default_rolling_work > 0)', 'Rolling Work time must be positive'),
    ]

    company_id = fields.Many2one('res.company', "Company_id", default=lambda self: self.env.company, store=True)
    company_name = fields.Char('CompanyName', store=False, required=False, related='company_id.name')
    rocker_default_start = fields.Float('Default Start Time [UTC]', store=True, readonly=False,
                                        help="Office start time")
    rocker_default_stop = fields.Float('Default Stop Time [UTC]', store=True, readonly=False, help="Office end time")
    rocker_default_work = fields.Float('Default Work amount', store=True, readonly=False,
                                       help="Work does not contain breaks like lunch hour")
    rocker_default_startToShow = fields.Float('Default Start Time [Local]', compute='_compute_show_start', store=False,
                                              readonly=False, help="Office start time")
    rocker_default_stopToShow = fields.Float('Default Stop Time [Local]', compute='_compute_show_stop', store=False,
                                             readonly=False, help="Office end time")
    # 2022
    rocker_round_up = fields.Selection([
        ('0', 'not'),
        ('5', '5 min'),
        ('10', '10 min'),
        ('15', '15 min'),
        ('30', '30 min'),
        ('60', '60 min')
        ], 'Round Amount To', required=False, default='0', store=True)
    rocker_default_rolling_work = fields.Float('Default Work amount if Rolling', store=True, readonly=False,
                                               help="Work does not contain breaks like lunch hour")

    @api.onchange('rocker_default_startToShow')
    def _onchange_rocker_default_startToShow(self):
        self.ensure_one()
        if self.rocker_default_startToShow < 0:
            self.rocker_default_startToShow = False
            self.rocker_default_start = False
            raise UserError(_('Start time negative'))
        self.rocker_default_start = self.to_UTC(self.rocker_default_startToShow)

    @api.onchange('rocker_default_stopToShow')
    def _onchange_rocker_default_stopToShow(self):
        self.ensure_one()
        if self.rocker_default_stopToShow < 0:
            self.rocker_default_stopToShow = False
            self.rocker_default_stop = False
            raise UserError(_('Stop time must be positive'))
        self.rocker_default_stop = self.to_UTC(self.rocker_default_stopToShow)

    @api.depends('rocker_default_startToShow')
    def _compute_show_start(self):
        _logger.debug('company compute_show_start')
        self.ensure_one()
        self.rocker_default_startToShow = self.to_LOCAL(self.rocker_default_start)

    @api.depends('rocker_default_stopToShow')
    def _compute_show_stop(self):
        _logger.debug('company compute_show_stop')
        self.ensure_one()
        self.rocker_default_stopToShow = self.to_LOCAL(self.rocker_default_stop)

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

    def to_LOCAL(self, dt):
        user = self.env.user
        if user.tz:
            tz = pytz.timezone(user.tz) or pytz.utc
            usertime = pytz.utc.localize(datetime.now()).astimezone(tz)
            offset = tz.utcoffset(datetime.now())
        else:
            tz = pytz.timezone('UTC')
            usertime = pytz.utc.localize(datetime.now()).astimezone(tz)
            offset = tz.utcoffset(datetime.now())

        return dt + offset.total_seconds() / 3600

    @api.model
    def edit_rocker_company_defaults(self):
        _default_id = self.env['rocker.company.defaults'].search([('company_id', '=', self.env.company.id)]).id
        if _default_id:
            return {
                'name': 'Edit Company Defaults',
                'res_model': 'rocker.company.defaults',
                'view_mode': 'form',
                'res_id': _default_id,
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_id': self.env.ref('rocker_timesheet.rocker_company_view_form_simplified').id,
                'target': 'new',
            }
        else:
            return {
                'name': 'Create Company Defaults',
                'res_model': 'rocker.company.defaults',
                'view_mode': 'form',
                # 'res_id':_default_id,
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_id': self.env.ref('rocker_timesheet.rocker_company_view_form_simplified').id,
                'target': 'new',
            }


class RockerUser(models.Model):
    _name = 'rocker.user.defaults'
    _description = 'Rocker User Defaults to Rocker Timesheet'
    _sql_constraints = [
        ('unique_defaults', 'unique (user_id,company_id)', 'Only one defaults per user per company!'),
        ('amount_positive', 'CHECK(rocker_default_work > 0)', 'Work must be positive'),
        ('rolling_work_positive', 'CHECK(rocker_default_rolling_work > 0)', 'Rolling Work time must be positive'),
    ]

    user_id = fields.Many2one('res.users', required=True, string='User_id', index=True,
                              default=lambda self: self.env.user, store=True)
    user_name = fields.Char('User', store=False, required=False, related='user_id.name')
    company_id = fields.Many2one('res.company', "Resource_Company", required=True,
                                 default=lambda self: self.env.company, store=True)
    employee_id = fields.Many2one('hr.employee', "Employee",
                                  default=lambda self: self.env['hr.employee'].search(
                                      [('user_id', '=', self.env.user.id),
                                       ('company_id', '=', self.env.company.id)]).id, store=True)
    department_id = fields.Many2one('hr.department', String="Resource Department", compute='_compute_department_id',
                                    store=True, compute_sudo=True)

    rocker_default_start = fields.Float('Default Start Time [UTC]', default='9', required=True, store=True,
                                        readonly=False, help="Office start time")
    rocker_default_stop = fields.Float('Default Stop Time [UTC]', default='17', required=True, store=True,
                                       readonly=False, help="Office end time")
    rocker_default_work = fields.Float('Default Work amount', required=True, store=True, readonly=False, default='7.5',
                                       help="Work does not contain breaks like lunch hour")
    rocker_default_startToShow = fields.Float('Default Start Time [Local]', default='9', compute='_compute_show_start',
                                              store=False, readonly=False, help="Office start time")
    rocker_default_stopToShow = fields.Float('Default Stop Time [Local]', default='17', compute='_compute_show_stop',
                                             store=False, readonly=False, help="Office end time")
    rocker_round_up = fields.Selection([
        ('0', 'not'),
        ('5', '5 min'),
        ('10', '10 min'),
        ('15', '15 min'),
        ('30', '30 min'),
        ('60', '60 min')
        ], 'Round Amount To', required=True, default='0', store=True)
    rocker_default_rolling_work = fields.Float('Default Work amount if Rolling', store=True, readonly=False,
                                               default='1', help="Work does not contain breaks like lunch hour")
    hourbank_calculation_start = fields.Date(
        String='Hourbank Calculation Start', required=False, readonly=False, store=True,
        default=datetime.today(), help="Start datetime for hourbank calculation")
    hourbank_initial_saldo = fields.Float(String='Hourbank initial saldo', store=True, readonly=False,
                                               default='0', help="Initial saldo for calculation start date")


    @api.depends('employee_id')
    def _compute_department_id(self):
        _logger.debug('compute_employee_id')
        self.ensure_one()
        self.department_id = self.employee_id.department_id

    @api.onchange('rocker_default_startToShow')
    def _onchange_rocker_default_startToShow(self):
        self.ensure_one()
        if self.rocker_default_startToShow < 0:
            self.rocker_default_startToShow = False
            self.rocker_default_start = False
            raise UserError(_('Start time negative'))
        self.rocker_default_start = self.to_UTC(self.rocker_default_startToShow)

    @api.onchange('rocker_default_stopToShow')
    def _onchange_rocker_default_stopToShow(self):
        self.ensure_one()
        if self.rocker_default_stopToShow < 0:
            self.rocker_default_stopToShow = False
            self.rocker_default_stop = False
            raise UserError(_('Stop time must be positive'))
        self.rocker_default_stop = self.to_UTC(self.rocker_default_stopToShow)

    @api.depends('rocker_default_startToShow')
    def _compute_show_start(self):
        _logger.debug('company compute_show_start')
        self.ensure_one()
        self.rocker_default_startToShow = self.to_LOCAL(self.rocker_default_start)

    @api.depends('rocker_default_stopToShow')
    def _compute_show_stop(self):
        _logger.debug('company compute_show_stop')
        self.ensure_one()
        self.rocker_default_stopToShow = self.to_LOCAL(self.rocker_default_stop)

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

    def to_LOCAL(self, dt):
        user = self.env.user
        if user.tz:
            tz = pytz.timezone(user.tz) or pytz.utc
            usertime = pytz.utc.localize(datetime.now()).astimezone(tz)
            offset = tz.utcoffset(datetime.now())
        else:
            tz = pytz.timezone('UTC')
            usertime = pytz.utc.localize(datetime.now()).astimezone(tz)
            offset = tz.utcoffset(datetime.now())

        return dt + offset.total_seconds() / 3600

    @api.model
    def edit_rocker_user_defaults(self):
        _default_id = self.env['rocker.user.defaults'].search(
            [('user_id', '=', self.env.user.id), ('company_id', '=', self.env.company.id)]).id
        if _default_id:
            return {
                'name': 'Edit User defaults',
                'res_model': 'rocker.user.defaults',
                'view_mode': 'form',
                'res_id': _default_id,
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_id': self.env.ref('rocker_timesheet.rocker_user_view_form_simplified').id,
                'target': 'new',
            }
        else:
            return {
                'name': 'Create User defaults',
                'res_model': 'rocker.user.defaults',
                'view_mode': 'form',
                # 'res_id':self._default_id,
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_id': self.env.ref('rocker_timesheet.rocker_user_view_form_simplified').id,
                'target': 'new',
            }
    @api.model
    def get_rocker_user_defaults(self, js_user_id, js_company_id):
        # called from javascript
        _user_defaults = self.env['rocker.user.defaults'].search(
            [('user_id', '=', js_user_id), ('company_id', '=', js_company_id)])

        _logger.debug('get_rocker_user_defaults')
        _logger.debug(_user_defaults)
        # _logger.debug(js_company_id)
        # _logger.debug(self.env.user.id)
        # _logger.debug(self.env.company.id)
        return [
            _user_defaults.user_id.id,
            _user_defaults.company_id.id,
            _user_defaults.rocker_calendar_default_view,
                ]
