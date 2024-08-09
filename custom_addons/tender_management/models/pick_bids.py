from odoo import api, fields, models, _


class Bid(models.Model):
    _name = 'pick.bid'
    _description = 'Pick Bid'

    name = fields.Char(string="Reference", copy=False, default='New', readonly=True)
    tender_id = fields.Many2one('tender.management', string="Tender")
    tender_user = fields.Many2one(string='Purchase Representative', related='tender_id.tender_user')
    date_created = fields.Date(string='Start Date', related='tender_id.date_created')
    date_bid_to_end = fields.Date(string='End Date', related='tender_id.date_bid_to_end')
    days_to_deadline = fields.Integer(string='Days Remaining', related='tender_id.days_to_deadline')
    bid_id = fields.Many2one('tender.id', string='Bids')
    pick_bid_management_line_ids = fields.One2many('pick.bid.management.line', 'pick_bid_management_id',
                                                   string='Pick Bid Management Line')
    state = fields.Selection([
        ('draft', 'DRAFT'),
        ('accept', 'SUBMITTED'),
        ('reject', 'APPROVE'),
    ], string='State', default='draft', required=True)

    def action_accept(self):
        self.change_state('accept')

    def action_reject(self):
        self.change_state('reject')

    def action_draft(self):
        self.change_state('draft')


class PickBidManagementLine(models.Model):
    _name = 'pick.bid.management.line'
    _description = "Pick Bid Management Line"

    bid_management_line_id = fields.Many2one('bid.management.line', string='Bid Management')

    product_id = fields.Many2one('product.product', string='Products', related='bid_management_line_id.product_id')
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        store=True, readonly=True,
    )
    product_quantity = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit Of Measure',
        store=True, readonly=True,
    )
    price_unit = fields.Float(string='Price', related='product_id.list_price', readonly=False)
    qty = fields.Integer(string='Quantity', related='bid_management_line_id.qty')
    default_code = fields.Char(related='product_id.default_code', string='Code')
    description = fields.Char(string='Description', related='bid_management_line_id.description')
    price_total = fields.Monetary(string='Total', related='bid_management_line_id.price_total')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.company.currency_id)
    pick_bid_management_id = fields.Many2one('pick.bid', string='Pick Bid')
