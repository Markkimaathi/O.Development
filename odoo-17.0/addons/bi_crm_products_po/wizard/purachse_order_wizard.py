from odoo import api, fields, models
from datetime import date

class Purchase(models.TransientModel):
    _name = "wizard.purchase"
    _description = "Description for wizard purchase"

    purchase_state = fields.Selection([
        ('rfq', 'Request For Quotation'),
        ('po', 'Purchase Order'),
    ], 'Purchase State', default="rfq")
    schedule_date = fields.Date(string="Schedule Date", default=lambda self: fields.datetime.now())

    def action_create_purchase_order(self):
        print('===========')
        line_list = []
        crm_id = self.env['crm.lead'].browse(self._context.get('active_id'))
        print("----------crm_id : ",crm_id)
        for crm_line in crm_id.crm_product_ids:
            vendor = crm_line.partner_id
            if vendor not in line_list:
                line_list.append(vendor)
                print('==========line_list',line_list)
        for partner in line_list:
            order_line= []
            crm_line_ids = self.env['crm.product.line'].search([('partner_id','=',partner.id),('crm_id','=',crm_id.id)])
            print('============crm_line_ids',crm_line_ids.read())
            if self.purchase_state == 'rfq':
                print('---------------------')
                for line in crm_line_ids:
                    order_line.append((0, 0, {
                                         'product_id'       : line.product_id.id,
                                         'product_qty'      : line.product_qty,
                                         'price_unit'       : line.price_unit,
                                         'date_planned'     : self.schedule_date,
                                         'product_uom'      : line.product_uom.id,
                                         'order_id'         : line.crm_id,
                                         'name'             : line.product_id.name,
                                         'taxes_id'        : [(6, 0, line.tax_id.ids)],
                                    }))
                    print('===========order_line==',order_line)
                purchase_obj = self.env['purchase.order']
                print('==line.partner_id.id :   ',line.partner_id.id)
                purchase_create_obj = purchase_obj.create({
                                        'partner_id': line.partner_id.id,
                                        'crm_id':line.crm_id.id,
                                        'state': "draft",
                                        'date_approve': self.schedule_date,
                                        'order_line': order_line,
                                        })
                print("purchase_create_obj - ",purchase_create_obj)

            elif self.purchase_state == 'po':
                for line in crm_line_ids:
                    order_line.append((0, 0, {
                                         'product_id'       : line.product_id.id,
                                         'product_qty'      : line.product_qty,
                                         'date_planned'     : self.schedule_date,
                                         'product_uom'      : line.product_uom.id,
                                         'order_id'         : line.crm_id,
                                         'price_unit'       : line.price_unit,
                                         'name'             : line.product_id.name,
                                         'taxes_id'        : [(6, 0, line.tax_id.ids)],
                                    }))
                purchase_obj = self.env['purchase.order']
                purchase_create_obj = purchase_obj.create({
                                        'partner_id': line.partner_id.id,
                                        'crm_id':line.crm_id.id,
                                        'state': "purchase",
                                        'date_approve': self.schedule_date,
                                        'order_line': order_line,
                                        })
                print("purchase_create_obj - ", purchase_create_obj)
        return True