from odoo import api, fields, models



class TenderBid(models.Model):
    _name = "tender.bid"
    _description = "Tender Bid"

    name = fields.Char(string="Bid")
    tender_id = fields.Many2one('tender.management', string="Tender", ondelete='cascade')