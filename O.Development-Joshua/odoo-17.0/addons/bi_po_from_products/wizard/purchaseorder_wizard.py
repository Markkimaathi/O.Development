from odoo import api, fields, models, _


class PurchaseOrderWizard(models.Model):
    _name = "purchase.order.wizard"
    _description = "Purchase Order Wizard"

    partner_id = fields.Many2one('res.partner', 'Vendor Name',
                                 index=True,
                                 required=True,)
    name_ids = fields.Many2many(
        'product.product', string='Services',)
    

    def action_confirm(self):
        self.ensure_one()
        order_line_ids=[]
        current_model = self.env.context.get('active_model')
        active_id = self.env[current_model].browse(self.env.context.get('active_ids'))
        for record in self:
            for rec in active_id:
                order_line_ids.append((0, 0, {
                        'product_id':rec.id,
                        'product_qty' : 1,
                 }))
            vals= ({   
                'partner_id': self.partner_id.id,
                'order_line':order_line_ids
            })
        invoice = self.env['purchase.order'].create(vals)
        return invoice
