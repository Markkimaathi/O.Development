# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, fields, models, _, Command
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, get_lang


class PurchaseRequestGroup(models.Model):
    _name = 'purchase.request.group'
    _description = "Technical model to group PO for call to tenders"

    order_ids = fields.One2many('purchase.rfq', 'purchase_group_id')

    def write(self, vals):
        res = super().write(vals)
        # when len(POs) == 1, only linking PO to itself at this point => self implode (delete) group
        self.filtered(lambda g: len(g.order_ids) <= 1).unlink()
        return res


class PurchaseRFQ(models.Model):
    _inherit = 'purchase.rfq'

    rfq_id = fields.Many2one('purchase.requisition', string='Blanket Order', copy=False)
    is_quantity_copy = fields.Selection(related='rfq_id.is_quantity_copy', readonly=False)

    purchase_group_id = fields.Many2one('purchase.request.group')
    alternative_po_ids = fields.One2many(
        'purchase.rfq', related='purchase_group_id.order_ids', readonly=False,
        domain="[('id', '!=', id), ('state', 'in', ['draft', 'sent', 'to approve'])]",
        string="Alternative POs", check_company=True,
        help="Other potential purchase orders for purchasing products")
    has_alternatives = fields.Boolean(
        "Has Alternatives", compute='_compute_has_alternatives',
        help="Whether or not this purchase order is linked to another purchase order as an alternative.")

    @api.depends('purchase_group_id')
    def _compute_has_alternatives(self):
        self.has_alternatives = False
        self.filtered(lambda po: po.purchase_group_id).has_alternatives = True

    @api.onchange('rfq_id')
    def _onchange_rfq_id(self):
        if not self.rfq_id:
            return

        self = self.with_company(self.company_id)
        requisition = self.rfq_id
        if self.partner_id:
            partner = self.partner_id
        else:
            partner = requisition.vendor_id
        payment_term = partner.property_supplier_payment_term_id

        FiscalPosition = self.env['account.fiscal.position']
        fpos = FiscalPosition.with_company(self.company_id)._get_fiscal_position(partner)

        self.partner_id = partner.id
        self.fiscal_position_id = fpos.id
        self.payment_term_id = payment_term.id
        self.company_id = requisition.company_id.id
        self.currency_id = requisition.currency_id.id
        if not self.origin or requisition.name not in self.origin.split(', '):
            if self.origin:
                if requisition.name:
                    self.origin = self.origin + ', ' + requisition.name
            else:
                self.origin = requisition.name
        self.notes = requisition.description
        self.date_order = fields.Datetime.now()

        if requisition.type_id.line_copy != 'copy':
            return

        # Create PO lines if necessary
        order_lines = []
        for line in requisition.line_ids:
            # Compute name
            product_lang = line.product_id.with_context(
                lang=partner.lang or self.env.user.lang,
                partner_id=partner.id
            )
            name = product_lang.display_name
            if product_lang.description_purchase:
                name += '\n' + product_lang.description_purchase

            # Compute taxes
            taxes_ids = fpos.map_tax(line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id)).ids

            # Compute quantity and price_unit
            if line.product_uom_id != line.product_id.uom_po_id:
                product_qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_po_id)
                price_unit = line.product_uom_id._compute_price(line.price_unit, line.product_id.uom_po_id)
            else:
                product_qty = line.product_qty
                price_unit = line.price_unit

            if requisition.type_id.quantity_copy != 'copy':
                product_qty = 0

            # Create PO line
            order_line_values = line._prepare_purchase_order_line(
                name=name, product_qty=product_qty, price_unit=price_unit,
                taxes_ids=taxes_ids)
            order_lines.append((0, 0, order_line_values))
        self.order_line = order_lines

    def button_confirm(self):
        if self.alternative_po_ids and not self.env.context.get('skip_alternative_check', False):
            alternative_po_ids = self.alternative_po_ids.filtered(lambda po: po.state in ['draft', 'sent', 'to approve'] and po.id not in self.ids)
            if alternative_po_ids:
                view = self.env.ref('purchase_requisition.purchase_requisition_alternative_warning_form')
                return {
                    'name': _("What about the alternative Requests for Quotations?"),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'purchase.requisition.alternative.warning',
                    'views': [(view.id, 'form')],
                    'target': 'new',
                    'context': dict(self.env.context, default_alternative_po_ids=alternative_po_ids.ids, default_po_ids=self.ids),
                }
        res = super(PurchaseRFQ, self).button_confirm()
        for po in self:
            if not po.rfq_id:
                continue
            if po.rfq_id.type_id.exclusive == 'exclusive':
                others_po = po.rfq_id.mapped('purchase_ids').filtered(lambda r: r.id != po.id)
                others_po.button_cancel()
                if po.state not in ['draft', 'sent', 'to approve']:
                    po.rfq_id.action_done()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        if self.env.context.get('origin_po_id'):
            # po created as an alt to another PO:
            origin_po_id = self.env['purchase.rfq'].browse(self.env.context.get('origin_po_id'))
            if origin_po_id.purchase_group_id:
                origin_po_id.purchase_group_id.order_ids |= orders
            else:
                self.env['purchase.request.group'].create({'order_ids': [Command.set(origin_po_id.ids + orders.ids)]})
        for order in orders:
            if order.rfq_id:
                order.message_post_with_source(
                    'mail.message_origin_link',
                    render_values={'self': order, 'origin': order.rfq_id},
                    subtype_xmlid='mail.mt_note',
                )
        return orders

    def write(self, vals):
        if vals.get('purchase_group_id', False):
            # store in case linking to a PO with existing linkages
            orig_purchase_group = self.purchase_group_id
        result = super(PurchaseRFQ, self).write(vals)
        if vals.get('rfq_id'):
            for order in self:
                order.message_post_with_source(
                    'mail.message_origin_link',
                    render_values={'self': order, 'origin': order.rfq_id, 'edit': True},
                    subtype_xmlid='mail.mt_note',
                )
        if vals.get('alternative_po_ids', False):
            if not self.purchase_group_id and len(self.alternative_po_ids + self) > len(self):
                # this can create a new group + delete an existing one (or more) when linking to already linked PO(s), but this is
                # simplier than additional logic checking if exactly 1 exists or merging multiple groups if > 1
                self.env['purchase.request.group'].create({'order_ids': [Command.set(self.ids + self.alternative_po_ids.ids)]})
            elif self.purchase_group_id and len(self.alternative_po_ids + self) <= 1:
                # write in purchase group isn't called so we have to manually unlink obsolete groups here
                self.purchase_group_id.unlink()
        if vals.get('purchase_group_id', False):
            # the write is for multiple POs => don't double count the POs of the final group
            additional_groups = orig_purchase_group - self.purchase_group_id
            if additional_groups:
                additional_pos = (additional_groups.order_ids - self.purchase_group_id.order_ids)
                additional_groups.unlink()
                if additional_pos:
                    self.purchase_group_id.order_ids |= additional_pos

        return result

    def action_create_alternative(self):
        ctx = dict(**self.env.context, default_origin_po_id=self.id)
        return {
            'name': _('Create alternative'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.requisition.create.alternative',
            'view_id': self.env.ref('purchase_requisition.purchase_requisition_create_alternative_form').id,
            'target': 'new',
            'context': ctx,
        }

    def action_compare_alternative_lines(self):
        ctx = dict(
            self.env.context,
            search_default_groupby_product=True,
            purchase_order_id=self.id,
        )
        view_id = self.env.ref('purchase_requisition.purchase_order_line_compare_tree').id
        return {
            'name': _('Compare Order Lines'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list',
            'res_model': 'purchase.rfq.line',
            'views': [(view_id, "list")],
            'domain': [('order_id', 'in', (self | self.alternative_po_ids).ids), ('display_type', '=', False)],
            'context': ctx,
        }

    def get_tender_group_id(self):
        if not self.purchase_group_id:
            return self.env['purchase.request.group']
        return self.purchase_group_id

    def action_rfq_send(self):
        if self.has_alternatives:
            context = {
                'default_model': 'purchase.rfq',
                'default_res_id': self.id,
                'default_res_ids': self.ids,
                'default_use_template': bool(self.env.context.get('use_template', False)),
                'default_mark_rfq_as_sent': True,
                'custom_layout': "mail.mail_notification_paynow",
                'proforma': self.env.context.get('proforma', False),
            }
            return self.env['mail.template'].with_context(**context).get_mail_template('purchase_requisition.alternative_rfq_mail')
        return super().action_rfq_send()
