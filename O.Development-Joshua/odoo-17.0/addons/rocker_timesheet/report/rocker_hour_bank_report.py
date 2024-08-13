# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.osv import expression


class RockerHourBankReport(models.Model):
    _name = "rocker.hour.bank.report"
    _description = 'Rocker Employee Hours Summary / Report'
    _auto = False
    _order = "employee_id, calendar_date asc "

    calendar_date = fields.Date('Date', readonly=True)
    name = fields.Char('Description', readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True)
    user_id = fields.Many2one('res.users', string="User", readonly=True)
    # resource_id = fields.Many2one('resource.resource', string="Resource", readonly=True)
    company_id = fields.Many2one('res.company', string="Company", readonly=True, default=lambda self: self.env.company)
    # resource_calendar_id = fields.Many2one('resource.calendar', string="Calendar", readonly=True)
    hours_per_day_required = fields.Float('Required Hours', readonly=True)
    unit_amount_per_day = fields.Float('Work Done', readonly=True)
    hour_saldo = fields.Float('Hour Saldo', readonly=True)
    # place_holder = fields.Char(' ', readonly=True)
    hourbank_calculation_start_date = fields.Date('Calculation Start Date', readonly=True)
    hourbank_initial_saldo = fields.Float('Initial Saldo at Start Date', readonly=True)

    def init(self):
        # tools.drop_view_if_exists(self._cr, 'rocker_hour_bank_report')
        tools.drop_view_if_exists(self.env.cr, self._table)

        # self._cr.execute("""
        self.env.cr.execute("""
        	CREATE or REPLACE view rocker_hour_bank_report as (
                    with rocker_calendar as (
                        select 
        				calendar_dates.calendar_date
        				,calendar_dates.user_id
                        ,he."id" as employee_id
                        ,he.company_id
                        ,he.resource_id
                        ,he.resource_calendar_id
                        ,rc."name" as calendar_name
                        ,ph.puclic_holiday_name
                        ,ph.is_public_holiday
                        ,ph.date_from as holiday_date_from
                        ,ph.date_to as holiday_date_to
                        ,ph.time_from as holiday_time_from
                        ,ph.time_to as holiday_time_to
        				,COALESCE((SELECT ROUND(CAST(SUM(hour_to - hour_from) as numeric),2)
                                FROM public.resource_calendar_attendance rca
                                   WHERE rca.calendar_id =  he.resource_calendar_id
                                   AND rca.dayofweek = cast((extract(isodow from calendar_dates.calendar_date) - 1) as varchar)
                                GROUP BY calendar_id, dayofweek
                                   ), 0) as calendar_hours_per_day
        				,ph.holiday_hours_per_day 
                       from (
        					 select calendar_date, 
        					 rr.user_id as user_id
        					 from resource_resource rr
        					 join (select generate_series (
        								(select min(date) from public.account_analytic_line)::timestamp,
        								(now() - interval '1 day')::timestamp,
        								 interval '1 day'
        								)::date as calendar_date
        						   ) aa on 1=1
        					join 			
        					(select user_id, COALESCE((select hourbank_calculation_start
                               from rocker_user_defaults rud
                               where rud.user_id = aal1.user_id
                              ),min(date)) minimi_date 
                                 from public.account_analytic_line aal1
                                 group by user_id) aal on aal.user_id = rr.user_id
                                where calendar_date >= minimi_date
                                ) calendar_dates

        				join public.hr_employee he on he.user_id = calendar_dates.user_id			 
                        join public.resource_calendar rc on he.resource_calendar_id = rc.id
                        left outer join (
                            select generate_series (
                                (date(date_from)),
                                (date(date_to)),
                                interval '1 day'
                                )::date as public_holiday_date, "name" as puclic_holiday_name, true as is_public_holiday, 
                                           date_from::time as time_from, date_to::time as time_to, date_from, date_to,
                                           round( CAST(float8 
                                                (
                                                DATE_PART('hour', date_to - date_from)::float + 
                                                DATE_PART('minute', date_to - date_from )/60::float + 
                                                DATE_PART('second', date_to - date_from )/3600::float
                                                ) as numeric)
                                                ,2)
                                                AS holiday_hours_per_day
                                from public.resource_calendar_leaves rcl
                                where resource_id is null 
                                ) ph on ph.public_holiday_date = calendar_dates.calendar_date
        			)
                        select 
                        row_number() over(ORDER BY rocker_hours.employee_id) as id
                        ,rocker_hours.calendar_date
                        ,rocker_hours.employee_id
                        ,rocker_hours.user_id
                        ,rocker_hours.company_id
                        ,rocker_hours.resource_id
                        ,rocker_hours.resource_calendar_id
                        ,rocker_hours.calendar_name
                        ,rocker_hours.calendar_hours_per_day
                        ,rocker_hours.puclic_holiday_name
                        ,rocker_hours.is_public_holiday
                        ,rocker_hours.holiday_date_from
                        ,rocker_hours.holiday_date_to
                        ,rocker_hours.holiday_time_from
                        ,rocker_hours.holiday_time_to
                        ,rocker_hours.holiday_hours_per_day
        				,rocker_hours.is_unpaid_leave
                        ,rocker_hours.name
        				,rocker_hours.hours_per_day_required
                        ,rocker_hours.unit_amount_per_day
                        ,ROUND(CAST((COALESCE(rocker_hours.unit_amount_per_day,0) - 
                                     COALESCE(rocker_hours.hours_per_day_required,0)) as numeric), 2)
									 + COALESCE((select hourbank_initial_saldo
                               from rocker_user_defaults rud
                               where rud.user_id = rocker_hours.user_id
						  		and rud.hourbank_calculation_start = rocker_hours.calendar_date
                              ),0) as hour_saldo
					    ,COALESCE((select hourbank_initial_saldo
                               from rocker_user_defaults rud
                               where rud.user_id = rocker_hours.user_id
						  		and rud.hourbank_calculation_start = rocker_hours.calendar_date
                              ),0) as hourbank_initial_saldo 
					    ,(select hourbank_calculation_start
                               from rocker_user_defaults rud
                               where rud.user_id = rocker_hours.user_id
						  		and rud.hourbank_calculation_start = rocker_hours.calendar_date
                              ) as hourbank_calculation_start_date 
                         from 
                        (
                        select 
                        roc_cal.calendar_date
                        ,roc_cal.employee_id
                        ,roc_cal.user_id
                        ,roc_cal.company_id
                        ,roc_cal.resource_id
                        ,roc_cal.resource_calendar_id
                        ,roc_cal.calendar_name
                        ,roc_cal.calendar_hours_per_day
                        ,roc_cal.puclic_holiday_name
                        ,roc_cal.is_public_holiday
                        ,roc_cal.holiday_date_from
                        ,roc_cal.holiday_date_to
                        ,roc_cal.holiday_time_from
                        ,roc_cal.holiday_time_to
                        ,roc_cal.holiday_hours_per_day
                        ,string_agg(aal."name", '; ') as name
                        ,CASE 
                            WHEN roc_cal.holiday_hours_per_day is null THEN roc_cal.calendar_hours_per_day
                            WHEN roc_cal.holiday_hours_per_day >= roc_cal.calendar_hours_per_day THEN 0
                            ELSE roc_cal.calendar_hours_per_day - roc_cal.holiday_hours_per_day
                          END as hours_per_day_required
        				, (select unpaid 
        				   from public.hr_leave_type 
        				   where id = (select holiday_status_id from public.hr_leave where id = aal.holiday_id)
        				  ) as is_unpaid_leave 
                        ,aal.unit_amount * COALESCE((select (NOT unpaid)::int 
        				   from public.hr_leave_type 
        				   where id = (select holiday_status_id from public.hr_leave where id = aal.holiday_id)
        				  ),1) as unit_amount_per_day

                        from rocker_calendar roc_cal
                        left outer join public.account_analytic_line aal 
                                 on (
                                     aal."date" = roc_cal.calendar_date
                                     and aal.company_id = roc_cal.company_id
                                     and aal.user_id = roc_cal.user_id
                                     and aal.employee_id = roc_cal.employee_id
                                     )
                        group by unit_amount_per_day, roc_cal.calendar_date 
                                ,roc_cal.user_id 
                                ,roc_cal.employee_id
                                ,roc_cal.company_id
                                ,roc_cal.resource_id
                                ,roc_cal.resource_calendar_id
                                ,roc_cal.calendar_name
                                ,roc_cal.calendar_hours_per_day
                                ,roc_cal.puclic_holiday_name
                                ,roc_cal.is_public_holiday
                                ,roc_cal.holiday_date_from
                                ,roc_cal.holiday_date_to
                                ,roc_cal.holiday_time_from
                                ,roc_cal.holiday_time_to
                                ,roc_cal.holiday_hours_per_day
        					    ,is_unpaid_leave
        						,hours_per_day_required

                        ) rocker_hours order by user_id, calendar_date
                );
                """)

    def open_leave_type_form(self):
        rec_id = self.env.context.get('active_id')
        form_id = self.env.ref('hr_holidays.edit_holiday_status_form')
        return {
            'name': 'Edit Time Off Type',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave.type',
            'res_id':  rec_id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': form_id.id,
            'context': {},
            'target': 'main',
        }
