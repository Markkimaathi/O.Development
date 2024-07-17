from odoo import models, fields, api

class PurchaseRFQ(models.Model):
    _name = 'purchase.rfq'
    _description = 'Request for Quotation'

    rfq_ref = fields.Char(string='RFQ Reference', readonly=True, copy=False, default='New')
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True)
    order_line_ids = fields.One2many('purchase.rfq.line', 'rfq_ref', string='Order Lines')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, index=True, copy=False, default='draft')
    date_planned = fields.Datetime(string='Scheduled Date', required=True, copy=False, default=fields.Datetime.now)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id.id)
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_compute_amount_total')

    @api.depends('order_line_ids.price_subtotal')
    def _compute_amount_total(self):
        for rfq in self:
            rfq.amount_total = sum(line.price_subtotal for line in rfq.order_line_ids)

    def action_done(self):
       for rec in self:
           rec.state = 'done'
    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancel'})
    def action_draft(self):
        for rec in self:
            rec.state = 'draft'


class PurchaseRFQLine(models.Model):
    _name = 'purchase.rfq.line'
    _description = 'RFQ Line'

    rfq_ref = fields.Many2one('purchase.rfq', string='RFQ Reference', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float(string='Quantity', required=True)
    price_unit = fields.Float(string='Unit Price')
    price_subtotal = fields.Monetary(string='Subtotal', store=True, readonly=True, compute='_compute_price_subtotal')
    currency_id = fields.Many2one(related='rfq_ref.currency_id', store=True, readonly=True)

    @api.depends('product_qty', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.product_qty * line.price_unit
