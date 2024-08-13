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
# from odoo import tools
from datetime import timedelta, datetime, date, time, timezone
import pytz
import urllib.request
import json


import logging

_logger = logging.getLogger(__name__)


class RockerHolidaysStaging(models.Model):
    _name = 'rocker.holidays.staging'
    _description = 'Rocker Import Public Holidays'
    _order = 'holiday_date'

    holiday_year = fields.Char('Year', readonly=False)
    country_code = fields.Char('Country Code', readonly=False)
    country_name = fields.Char('Country Name', readonly=False)
    holiday_date = fields.Date('Date', readonly=False)
    name_local = fields.Char('Holiday [in local lang]', readonly=False)
    name_other = fields.Char('Holiday [in other lang]', readonly=False)
    holiday_type = fields.Char('Holiday type', readonly=False)
    main_class_id = fields.Many2one('rocker.holidays', string="Main Class")


class RockerHolidays(models.Model):
    _name = 'rocker.holidays'
    _description = 'Rocker Import Public Holidays'
    _order = 'date_executed'

    date_executed = fields.Datetime('Date Executed', readonly=False, default=lambda self: fields.datetime.now())
    notebook_ids = fields.One2many('rocker.holidays.staging', 'main_class_id', string="Imported Public Holidays")

    holiday_year = fields.Selection(
        selection='years_selection',
        string="Public Holidays for Year",
        default=str(datetime.now().year))
    holiday_country = fields.Selection(
        selection='country_selection',
        string="Public Holidays for Country",
        default='fin')
    write_local = fields.Selection([
        ('local', 'Local Language'),
        ('other', 'Other Language'),
        ], string='Take', store=True, required=False, default='local')

    @api.model
    def create(self, vals):
        _logger.debug('Create')
        # vals = {}
        return super(RockerHolidays, self.sudo()).create(vals)
        # return vals

    def write(self, vals):
        _logger.debug('Write')
        # vals = {}
        return super(RockerHolidays, self.sudo()).write(vals)
        # return vals

    @api.model
    def years_selection(self):
        year_list = []
        for y in range(datetime.now().year, datetime.now().year + 10):
            year_list.append((str(y), str(y)))
        return year_list

    @api.model
    def country_selection(self):
        _logger.debug(self)
        country_list = []
        country_list = self.get_countries()
        return country_list

    # https://kayaposoft.com/enrico/json/v2.0?action=getSupportedCountries

    @api.model
    def get_countries(self):
        _logger.debug('Get country...')
        country_list = []
        countries = ''
        countries_details = None
        url = 'https://kayaposoft.com/enrico/json/v2.0?action=getSupportedCountries'
        try:
            with urllib.request.urlopen(url) as f:
                # _logger.debug(f.read().decode('utf-8'))
                countries = f.read().decode('utf-8')
                # _logger.debug(countries)
        except urllib.error.URLError as e:
            _logger.debug(e.reason)

        countries_details = json.loads(countries)

        for i in countries_details:
            c_code = i['countryCode']
            c_fullname = i["fullName"]
            # _logger.debug(c_code)
            regions = i['regions']
            if len(regions) > 0:
                for j in regions:
                    # _logger.debug(j)
                    # _logger.debug(c_fullname + '[' + j + ']')
                    # _logger.debug(c_code + ',' + j)
                    country_list.append((c_code + ',' + j, c_fullname + '[' + j + ']'))
            else:
                country_list.append((c_code, c_fullname))

        return country_list

    def import_holidays(self):
        # _logger.debug('Import holidays...')
        _id = None
        _year = None
        _holiday_country = None
        _country_code = None
        _region_code = None
        _country_name = None

        context = dict(self.env.context)
        _logger.debug(context)
        _id = context.get('id')
        _year = context.get('holiday_year')
        _holiday_country = context.get('holiday_country')
        _country_name = dict(self.fields_get(allfields=['holiday_country'])['holiday_country']['selection'])[
            context.get('holiday_country')]
        if _holiday_country.find(',') > 0:
            _country_code = _holiday_country.split(',')[0]
            _region_code = _holiday_country.split(',')[1]
        else:
            _country_code = _holiday_country
            _region_code = None

        _logger.debug(_country_code)
        _logger.debug(_region_code)
        # create header
        # remove old rows: country & year
        _delete = "DELETE FROM rocker_holidays_staging WHERE holiday_year = '" + _year + "' and country_code = '" \
                  + _country_code + "' and main_class_id != " + str(_id)
        _logger.debug(_delete)
        ret = self.env.cr.execute(_delete)
        _delete = "DELETE FROM rocker_holidays WHERE holiday_year = '" + _year + "' and holiday_country = '" \
                  + _country_code + "' and id != " + str(_id)
        _logger.debug(_delete)
        ret = self.env.cr.execute(_delete)
        holidays = ''
        if _region_code:
            url = 'https://kayaposoft.com/enrico/json/v2.0/?action=getHolidaysForYear&year=' + _year + \
                  '&country=' + _country_code + '&region=' + _region_code + '&holidayType=public_holiday'
        else:
            url = 'https://kayaposoft.com/enrico/json/v2.0/?action=getHolidaysForYear&year=' + _year + \
                  '&country=' + _country_code + '&holidayType=public_holiday'
        try:
            with urllib.request.urlopen(url) as f:
                # _logger.debug(f.read().decode('utf-8'))
                holidays = f.read().decode('utf-8')
                _logger.debug(holidays)

        except urllib.error.URLError as e:
            _logger.debug(e.reason)

        _date = None
        _holiday_date = None
        _name = None
        _name_local = None
        _name_other = None
        _holiday_type = None
        _hol_record = None

        vals = {}

        holiday_details = json.loads(holidays)

        for i in holiday_details:
            # _logger.debug(i)
            _date = i['date']
            # _logger.debug(_date)
            _holiday_date = date(int(_date['year']), int(_date['month']), int(_date['day']))
            # _logger.debug(_holiday_date)
            _name = i["name"]
            # _logger.debug(_name)
            _name_local = _name[0]
            _name_local = _name_local['text']
            # _logger.debug(len(_name))
            if len(_name) > 1:
                _name_other = _name[1]
                _name_other = _name_other['text']
            else:
                _name_other = _name_local
            # _logger.debug(_name_local)
            # _logger.debug(_name_other)
            _holiday_type = i["holidayType"]

            vals = {
                'holiday_year': _year,
                'country_code': _country_code,
                'country_name': _country_name,
                'holiday_date': _holiday_date,
                'name_local': _name_local,
                'name_other': _name_other,
                'holiday_type': _holiday_type,
                'main_class_id': _id
            }
            _hol_record = self.env['rocker.holidays.staging'].create(vals)

        self.env.cr.commit()

        rec_id = _id
        form_id = self.env.ref('rocker_timesheet.rocker_holidays_view_form')
        context['form_view_initial_mode'] = 'edit'
        return {
            'name': 'Imported Public Holiday',
            'type': 'ir.actions.act_window',
            'res_model': 'rocker.holidays',
            'res_id': rec_id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': form_id.id,
            'context': context,
            'target': 'inline',
        }

    def export_holidays(self):
        _logger.debug('Export holidays...')
        context = self.env.context
        _company_id = self.env.company.id
        _id = None
        _year = None
        _lang = None
        _local = None
        _country_code = None
        _country_name = None
        _id = context.get('id')
        _lang = context.get('write_local')
        _year = context.get('holiday_year')
        _country_code = context.get('holiday_country')
        _country_name = dict(self.fields_get(allfields=['holiday_country'])['holiday_country']['selection'])[
                        context.get('holiday_country')]
        _logger.debug(_lang)
        if _lang == 'local':
            _local = 'rhs.name_local'
        else:
            _local = 'rhs.name_other'

        if self.env.user.tz:
            tz = pytz.timezone(self.env.user.tz) or pytz.utc
        else:
            tz = pytz.timezone('UTC')
        _logger.debug(tz)

        _update = """update resource_calendar_leaves rcl
                    set name = """ + _local + """
                    ,date_from = rhs.holiday_date::timestamp AT TIME ZONE '%s' AT TIME ZONE 'UTC'
                    ,date_to = ((rhs.holiday_date + 1)::timestamp -interval '1 second')  
                                 AT TIME ZONE '%s'  AT TIME ZONE 'UTC'   
                    from rocker_holidays_staging rhs
                    where (rcl.date_from::timestamp  AT TIME ZONE 'UTC')::date = rhs.holiday_date
                    and (rcl.date_from::timestamp  AT TIME ZONE 'UTC')::date = rhs.holiday_date
                    and rhs.country_code = '%s'
                    and rhs.main_class_id = %d
                    and rcl.company_id = %d
                    and rcl.resource_id is null""" % (tz, tz, _country_code, _id, _company_id)
        _insert = """insert into resource_calendar_leaves (company_id, name, date_from, date_to, time_type)
                    select 1, """ + _local + """, holiday_date::timestamp AT TIME ZONE '%s' AT TIME ZONE 'UTC' , 
                           ((holiday_date + 1)::timestamp -interval '1 second')  AT TIME ZONE '%s'  AT TIME ZONE 'UTC',
                            'leave'
                    from rocker_holidays_staging rhs
                    where rhs.holiday_date not in (select (rcl.date_from::timestamp  AT TIME ZONE 'UCT')::date 
                                                   from resource_calendar_leaves rcl
                                                   where rcl.company_id = %d
                                                   and rcl.resource_id is null)
                    
                    and rhs.country_code = '%s'
                    and rhs.main_class_id = %d
                    """ % (tz, tz, _company_id, _country_code, _id)
        _logger.debug(_update)
        _logger.debug(_insert)
        try:
            ret = self.env.cr.execute(_update)
            ret = self.env.cr.execute(_insert)
            self.env.cr.commit()
        except Exception as e:
            raise exceptions.ValidationError(str(e))
            return False


        rec_id = None
        form_id = self.env.ref('resource.action_resource_calendar_leave_tree')
        # context = None
        return {
            'name': 'Public Holidays',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'resource.calendar.leaves',
            'context': {'no_breadcrumbs': True},
        }

    def clear_form(self):
        _logger.debug('Export holidays...')
        context = self.env.context
        rec_id = None
        form_id = self.env.ref('rocker_timesheet.rocker_holidays_view_form')
        return {
            'name': 'Import Public Holidays',
            'type': 'ir.actions.act_window',
            'res_model': 'rocker.holidays',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': rec_id,
            'view_id': form_id.id,
            'context': {},
            'target': 'inline',
        }
