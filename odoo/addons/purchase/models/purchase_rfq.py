# purchase_custom/models/rfq.py
from odoo import models, fields, api, _


class PurchaseRFQ(models.Model):
    _name = 'purchase.rfq'
    _description = 'Request for Quotation'

    name = fields.Char(string='RFQ Reference', required=True, copy=False, default='New')
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True)
    order_line_ids = fields.One2many('purchase.rfq.line', 'rfq_id', string='Order Lines')
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

    def action_confirm(self):
        self.ensure_one()
        po_vals = {
            'partner_id': self.partner_id.id,
            'date_planned': self.date_planned,
            'rfq_id': self.id,
            'order_line': [(0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.product_qty,
                'price_unit': line.price_unit,
            }) for line in self.order_line_ids]
        }
        po = self.env['purchase.order'].create(po_vals)
        self.write({'state': 'done'})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'res_model': 'purchase.order',
            'res_id': po.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancel'})

class PurchaseRFQLine(models.Model):
    _name = 'purchase.rfq.line'
    _description = 'RFQ Line'

    rfq_id = fields.Many2one('purchase.rfq', string='RFQ Reference', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float(string='Quantity', required=True)
    price_unit = fields.Float(string='Unit Price')
    price_subtotal = fields.Monetary(string='Subtotal', store=True, readonly=True, compute='_compute_price_subtotal')
    currency_id = fields.Many2one(related='rfq_id.currency_id', store=True, readonly=True)

    @api.depends('product_qty', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.product_qty * line.price_unit
