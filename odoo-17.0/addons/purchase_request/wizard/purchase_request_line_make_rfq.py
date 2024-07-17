from datetime import datetime
import pytz
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import get_lang


class PurchaseRequestLineMakeRFQ(models.TransientModel):
    _name = "purchase.request.line.make.rfq"
    _description = "Purchase Request Line Make RFQ"

    supplier_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier",
        required=True,
        context={"res_partner_search_mode": "supplier"},
    )
    item_ids = fields.One2many(
        comodel_name="purchase.request.line.make.rfq.item",
        inverse_name="wiz_id",
        string="Items",
    )
    purchase_rfq_id = fields.Many2one(
        comodel_name="purchase.rfq",
        string="Purchase RFQ",
        domain=[("state", "=", "draft")],
    )
    sync_data_planned = fields.Boolean(
        string="Match existing RFQ lines by Scheduled Date",
        help=(
            "When checked, RFQ lines on the selected purchase RFQ are only reused "
            "if the scheduled date matches as well."
        ),
    )

    @api.model
    def _prepare_item(self, line):
        return {
            "line_id": line.id,
            "request_id": line.request_id.id,
            "product_id": line.product_id.id,
            "name": line.name or line.product_id.name,
            "product_qty": line.pending_qty_to_receive,
            "product_uom_id": line.product_uom_id.id,
        }

    @api.model
    def _check_valid_request_line(self, request_line_ids):
        picking_type = False
        company_id = False

        for line in self.env["purchase.request.line"].browse(request_line_ids):
            if line.request_id.state == "done":
                raise UserError(_("The purchase has already been completed."))
            if line.request_id.state != "approved":
                raise UserError(
                    _("Purchase Request %s is not approved") % line.request_id.name
                )

            if line.purchase_state == "done":
                raise UserError(_("The purchase has already been completed."))

            line_company_id = line.company_id and line.company_id.id or False
            if company_id is not False and line_company_id != company_id:
                raise UserError(_("You have to select lines from the same company."))
            else:
                company_id = line_company_id

            line_picking_type = line.request_id.picking_type_id or False
            if not line_picking_type:
                raise UserError(_("You have to enter a Picking Type."))
            if picking_type is not False and line_picking_type != picking_type:
                raise UserError(
                    _("You have to select lines from the same Picking Type.")
                )
            else:
                picking_type = line_picking_type

    @api.model
    def check_group(self, request_lines):
        if len(list(set(request_lines.mapped("request_id.group_id")))) > 1:
            raise UserError(
                _(
                    "You cannot create a single purchase RFQ from "
                    "purchase requests that have different procurement group."
                )
            )

    @api.model
    def get_items(self, request_line_ids):
        request_line_obj = self.env["purchase.request.line"]
        items = []
        request_lines = request_line_obj.browse(request_line_ids)
        self._check_valid_request_line(request_line_ids)
        self.check_group(request_lines)
        for line in request_lines:
            items.append([0, 0, self._prepare_item(line)])
        return items

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        active_model = self.env.context.get("active_model", False)
        request_line_ids = []
        if active_model == "purchase.request.line":
            request_line_ids += self.env.context.get("active_ids", [])
        elif active_model == "purchase.request":
            request_ids = self.env.context.get("active_ids", False)
            request_line_ids += (
                self.env[active_model].browse(request_ids).mapped("line_ids.id")
            )
        if not request_line_ids:
            return res
        res["item_ids"] = self.get_items(request_line_ids)
        request_lines = self.env["purchase.request.line"].browse(request_line_ids)
        supplier_ids = request_lines.mapped("supplier_id").ids
        if len(supplier_ids) == 1:
            res["supplier_id"] = supplier_ids[0]
        return res

    @api.model
    def _prepare_purchase_rfq(self, picking_type, group_id, company, origin):
        if not self.supplier_id:
            raise UserError(_("Enter a supplier."))

        # Debug print to check the origin value
        print("Origin value:", origin)

        supplier = self.supplier_id
        data = {
            "origin": origin,  # Ensure 'origin' is correctly populated here
            "partner_id": self.supplier_id.id,
            "payment_term_id": self.supplier_id.property_supplier_payment_term_id.id,
            "fiscal_position_id": supplier.property_account_position_id
                                  and supplier.property_account_position_id.id
                                  or False,
            "picking_type_id": picking_type.id,
            "company_id": company.id,
            "group_id": group_id.id,
        }
        return data

    def create_allocation(self, rfq_line, pr_line, new_qty, alloc_uom):
        vals = {
            "requested_product_uom_qty": new_qty,
            "product_uom_id": alloc_uom.id,
            "purchase_request_line_id": pr_line.id,
            "purchase_line_id": rfq_line.id,
        }
        return self.env["purchase.request.allocation"].create(vals)

    @api.model
    def _prepare_purchase_rfq_line(self, rfq, item):
        if not item.product_id:
            raise UserError(_("Please select a product for all lines"))
        product = item.product_id

        # Keep the standard product UOM for purchase RFQ so we should
        # convert the product quantity to this UOM
        qty = item.product_uom_id._compute_quantity(
            item.product_qty, product.uom_po_id or product.uom_id
        )
        # Suggest the supplier min qty as it's done in Odoo core
        min_qty = item.line_id._get_supplier_min_qty(product, rfq.partner_id)
        qty = max(qty, min_qty)
        date_required = item.line_id.date_required
        return {
            "rfq_id": rfq.id,
            "product_id": product.id,
            "product_uom": product.uom_po_id.id or product.uom_id.id,
            "price_unit": 0.0,
            "product_qty": qty,
            "analytic_distribution": item.line_id.analytic_distribution,
            "purchase_request_lines": [(4, item.line_id.id)],
            "date_planned": datetime(
                date_required.year, date_required.month, date_required.day
            ),
            "move_dest_ids": [(4, x.id) for x in item.line_id.move_dest_ids],
        }

    @api.model
    def _get_purchase_line_name(self, rfq, line):
        """Fetch the product name as per supplier settings"""
        product_lang = line.product_id.with_context(
            lang=get_lang(self.env, self.supplier_id.lang).code,
            partner_id=self.supplier_id.id,
            company_id=rfq.company_id.id,
        )
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += "\n" + product_lang.description_purchase
        return name

    @api.model
    def _get_rfq_line_search_domain(self, rfq, item):
        vals = self._prepare_purchase_rfq_line(rfq, item)
        name = self._get_purchase_line_name(rfq, item)
        rfq_line_data = [
            ("rfq_id", "=", rfq.id),
            ("name", "=", name),
            ("product_id", "=", item.product_id.id),
            ("product_uom", "=", vals["product_uom"]),
            ("analytic_distribution", "=?", item.line_id.analytic_distribution),
        ]
        if self.sync_data_planned:
            date_required = item.line_id.date_required
            rfq_line_data += [
                (
                    "date_planned",
                    "=",
                    datetime(
                        date_required.year, date_required.month, date_required.day
                    ),
                )
            ]
        if not item.product_id:
            rfq_line_data.append(("name", "=", item.name))
        return rfq_line_data

    def make_purchase_rfq(self):
        res = []
        purchase_obj = self.env["purchase.rfq"]
        rfq_line_obj = self.env["purchase.rfq.line"]
        pr_line_obj = self.env["purchase.request.line"]
        user_tz = pytz.timezone(self.env.user.tz or "UTC")
        purchase = False

        for item in self.item_ids:
            line = item.line_id
            if item.product_qty <= 0.0:
                raise UserError(_("Enter a positive quantity."))
            if self.purchase_rfq_id:
                purchase = self.purchase_rfq_id
            if not purchase:
                po_data = self._prepare_purchase_rfq(
                    line.request_id.picking_type_id,
                    line.request_id.group_id,
                    line.company_id,
                    line.origin,
                )
                purchase = purchase_obj.create(po_data)

            # Look for any other RFQ line in the selected RFQ with same
            # product and UoM to sum quantities instead of creating a new
            # RFQ line
            domain = self._get_rfq_line_search_domain(purchase, item)
            available_rfq_lines = rfq_line_obj.search(domain)
            new_pr_line = True
            # If Unit of Measure is not set, update from wizard.
            if not line.product_uom_id:
                line.product_uom_id = item.product_uom_id
            # Allocation UoM has to be the same as PR line UoM
            alloc_uom = line.product_uom_id
            wizard_uom = item.product_uom_id
            if available_rfq_lines and not item.keep_description:
                new_pr_line = False
                rfq_line = available_rfq_lines[0]
                rfq_line.purchase_request_lines = [(4, line.id)]
                rfq_line.move_dest_ids |= line.move_dest_ids
                rfq_line_product_uom_qty = rfq_line.product_uom._compute_quantity(
                    rfq_line.product_uom_qty, alloc_uom
                )
                wizard_product_uom_qty = wizard_uom._compute_quantity(
                    item.product_qty, alloc_uom
                )
                all_qty = min(rfq_line_product_uom_qty, wizard_product_uom_qty)
                self.create_allocation(rfq_line, line, all_qty, alloc_uom)
            else:
                rfq_line_data = self._prepare_purchase_rfq_line(purchase, item)
                if item.keep_description:
                    rfq_line_data["name"] = item.name
                rfq_line = rfq_line_obj.create(rfq_line_data)
                rfq_line_product_uom_qty = rfq_line.product_uom._compute_quantity(
                    rfq_line.product_uom_qty, alloc_uom
                )
                wizard_product_uom_qty = wizard_uom._compute_quantity(
                    item.product_qty, alloc_uom
                )
                all_qty = min(rfq_line_product_uom_qty, wizard_product_uom_qty)
                self.create_allocation(rfq_line, line, all_qty, alloc_uom)
            # TODO: Check propagate_uom compatibility:
            new_qty = pr_line_obj._calc_new_qty(
                line, rfq_line=rfq_line, new_pr_line=new_pr_line
            )
            rfq_line.product_qty = new_qty
            # The quantity update triggers a compute method that alters the
            # unit price (which is what we want, to honor graduate pricing)
            # but also the scheduled date which is what we don't want.
            date_required = item.line_id.date_required
            # we enforce to save the datetime value in the current tz of the user
            rfq_line.date_planned = (
                user_tz.localize(
                    datetime(date_required.year, date_required.month, date_required.day)
                )
                .astimezone(pytz.utc)
                .replace(tzinfo=None)
            )
            res.append(purchase.id)

        return {
            "domain": [("id", "in", res)],
            "name": _("RFQ"),
            "view_mode": "tree,form",
            "res_model": "purchase.rfq",
            "view_id": False,
            "context": False,
            "type": "ir.actions.act_window",
        }


class PurchaseRequestLineMakeRFQItem(models.TransientModel):
    _name = "purchase.request.line.make.rfq.item"
    _description = "Purchase Request Line Make RFQ Item"

    wiz_id = fields.Many2one(
        comodel_name="purchase.request.line.make.rfq",
        string="Wizard",
        required=True,
        ondelete="cascade",
        readonly=True,
    )
    line_id = fields.Many2one(
        comodel_name="purchase.request.line", string="Purchase Request Line"
    )
    request_id = fields.Many2one(
        comodel_name="purchase.request",
        related="line_id.request_id",
        string="Purchase Request",
        readonly=False,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        related="line_id.product_id",
        readonly=False,
    )
    name = fields.Char(string="Description", required=True)
    product_qty = fields.Float(
        string="Quantity to purchase", digits="Product Unit of Measure"
    )
    product_uom_id = fields.Many2one(
        comodel_name="uom.uom", string="UoM", required=True
    )
    keep_description = fields.Boolean(
        string="Copy descriptions to new RFQ",
        help="Set true if you want to keep the "
        "descriptions provided in the "
        "wizard in the new RFQ.",
    )

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            if not self.keep_description:
                name = self.product_id.name
            code = self.product_id.code
            sup_info_id = self.env["product.supplierinfo"].search(
                [
                    "|",
                    ("product_id", "=", self.product_id.id),
                    ("product_tmpl_id", "=", self.product_id.product_tmpl_id.id),
                    ("partner_id", "=", self.wiz_id.supplier_id.id),
                ]
            )
            if sup_info_id:
                p_code = sup_info_id[0].product_code
                p_name = sup_info_id[0].product_name
                name = f"[{p_code if p_code else code}] {p_name if p_name else name}"
            else:
                if code:
                    name = f"[{code}] {self.name if self.keep_description else name}"
            if self.product_id.description_purchase and not self.keep_description:
                name += "\n" + self.product_id.description_purchase
            self.product_uom_id = self.product_id.uom_id.id
            if name:
                self.name = name
