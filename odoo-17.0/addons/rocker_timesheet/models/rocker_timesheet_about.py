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
import logging


_logger = logging.getLogger(__name__)


class rocker_timesheet_about(models.TransientModel):
    _name = "rocker.timesheet.about"
    _description = "Rocker Timesheet About box"
    name = fields.Html(string="Name", readonly=True, default="<H2>Rocker Timesheet</H2")
    paypal = fields.Html(string="PayPal", readonly=True, default='''
        <p>If you like this reporting app, please click:</b><br></p>''')
    donate = fields.Char(string="Donate", readonly=True,
        default="https://www.paypal.com/donate/?business=DGK3E2CC42EJ4&no_recurring=0&currency_code=EUR")
    legal = fields.Html(string="Legal", readonly=True, default='''<p>Author: Antti Kärki<br>
    Even small amounts are appreciated</p>
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation.
<p></p>
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
<p></p>
    https://www.gnu.org/licenses.
''')

    @api.model
    def _show_about(self):
        _logger.debug('Open About ')
        context = {}
        context['message'] = "Rocker Timesheet is nice"
        title = 'About Rocker Timesheet'
        view = self.env.ref('rocker_timesheet.rocker_timesheet_about')
        view_id = self.env.ref('rocker_timesheet.rocker_timesheet_about').id
        return {
            'name': title,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rocker.timesheet.about',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }
