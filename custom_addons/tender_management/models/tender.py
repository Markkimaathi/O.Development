from odoo import api, fields, models
from _datetime import date


class TenderManagement(models.Model):
    _name = "tender.management"
    _description = "Tender Management"
    # _inherit = ['mail.thread', 'mail.activity.mixin',]

    name = fields.Char(string="Tender")
    ref = fields.Char(string="Reference")
    # date_created = fields.Date(string='Start Date', default=fields.Datetime.now)
    # date_bid_to_end = fields.Date(string='End Date', default=fields.Date.context_today)