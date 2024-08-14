from odoo import api, fields, models
from datetime import date


class CrmProduct(models.Model):
    _name = 'crm.product.line'
    _description = "description for crm product line"

    product_id = fields.Many2one('product.product', string="Product")
    partner_id = fields.Many2one('res.partner', string="Vendor Name")
    product_qty = fields.Float(string="Quantity")
    price_unit = fields.Float(string="Unit Price")
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')  
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    tax_id = fields.Many2many('account.tax', string='Taxes')
    crm_id = fields.Many2one('crm.lead')


    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            product_id = self.env['product.product'].sudo().search([('id', '=', self.product_id.id)])
            for product in product_id.seller_ids:
                self.write({
                            'price_unit'                : self.product_id.lst_price,
                            'product_uom'               : self.product_id.uom_id.id,
                            'partner_id'                : product.partner_id.id,      
                          })  


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    crm_product_ids = fields.One2many('crm.product.line', 'crm_id', string="Product")
    purchase_order_count = fields.Integer(compute="_compute_po_count")

    def _compute_po_count(self):
        count = self.env['purchase.order'].sudo().search_count([('crm_id','=',self.id)])
        self.purchase_order_count = count

    def button_applicant_backend(self):
        return {
            'name': 'Purchase Order',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'domain': [('crm_id','=',self.id)]
        }


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    crm_id = fields.Many2one('crm.lead', string="CRM Lead")




