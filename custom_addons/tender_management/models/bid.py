from odoo import api, fields, models,_

class Bid(models.Model):
    _name = 'tender.bid'
    _description = 'Bid'

    def _get_default_user(self):
        return self.env.user.id

    name = fields.Many2one('res.users', string="Purchase Representative", default=_get_default_user)
    tender_id = fields.Many2one('tender.management', string="Tender", required=True)
    ref = fields.Char(string="Reference", copy=False, default='New', readonly=True)
    partner_id = fields.Many2many('res.partner', string="Vendor")
    date_created = fields.Date(string='Start Date', default=fields.Date.context_today)
    date_bid_to_end = fields.Date(sbid_amounttring='End Date', default=fields.Date.context_today)
    bid_management_line_ids = fields.One2many('bid.management.line', 'bid_management_id',
                                                 string='Tender Management Line')
    bid_ids = fields.One2many('tender.bid', 'tender_id', string="Bids")

    state = fields.Selection([
        ('draft', 'DRAFT'),
        ('submit', 'SUBMITTED'),
        ('approve', 'APPROVE'),
        ('approved', 'IN PROGRESS'),
        ('done', 'DONE'),
        ('cancel', 'CANCEL')], string='State', default='draft', required=True)

    def create(self, vals):
        if vals.get('ref', _('New')) == _('New'):
            vals['ref'] = self.env['ir.sequence'].next_by_code('tender.bid') or _('New')
        return super(Bid, self).create(vals)

    def _compute_bid_count(self):
        for tender in self:
            tender.bid_count = len(tender.bid_ids)

    def change_state(self, new_state):
        for rec in self:
            rec.state = new_state

    def action_approve(self):
        self.change_state('approve')

    def action_done(self):
        self.change_state('done')

    def action_cancel(self):
        self.change_state('cancel')

    def action_draft(self):
        self.change_state('draft')

    def action_approved(self):
        self.change_state('approved')

    def action_submit(self):
        self.change_state('submit')

class BidManagementLine(models.Model):
    _name = 'bid.management.line'
    _description = "Bid Management Line"

    product_id = fields.Many2one('product.product', string='Products')
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Product Uom',
        store=True, readonly=False,
    )
    product_quantity = fields.Many2one(
        comodel_name='uom.uom',
        string='Product Quantity',
        store=True, readonly=False,
    )
    price_unit = fields.Float(string='Price', related='product_id.list_price')
    qty = fields.Integer(string='Quantity')
    default_code = fields.Char(related='product_id.default_code', string='Code')
    description = fields.Char(string='Description')
    bid_management_id = fields.Many2one('tender.bid', string='Bid Management')