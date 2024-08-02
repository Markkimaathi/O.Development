from odoo import api, fields, models



class TenderBid(models.Model):
    _name = "tender.bid"
    _description = "Tender Bid"

    name = fields.Char(string="Name")
    bid_ref = fields.Char(string="Bid Reference", copy=False, default='New', readonly=True)
    bid_count=fields.Many2one('tender', string='Bids')
    tender_id = fields.Many2one('tender.management', string="Tender", ondelete='cascade')