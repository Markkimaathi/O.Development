from odoo import api, fields, models
from _datetime import date


class TenderManagement(models.Model):
    _name = "tender.management"
    _description = "Tender Management"
    _inherit = ['mail.thread', 'mail.activity.mixin',]

    name = fields.Many2one('res.users', string="Purchase Representative")
    ref = fields.Char(string="Reference", readonly=True, copy=False, default='New')
    partner_id = fields.Many2many('res.partner', string="Vendor")
    date_created = fields.Date(string='Start Date', default=fields.Datetime.now)
    date_bid_to_end = fields.Date(string='End Date', default=fields.Date.context_today)
    state = fields.Selection([
        ('draft', 'DRAFT'),
        ('submit', 'SUBMITTED'),
        ('approve', 'APPROVE'),
        ('approved', 'IN PROGRESS'),
        ('done', 'DONE'),
        ('cancel', 'CANCEL')], string='State', default='draft', required=True
    )
    days_to_deadline= fields.Integer(string='Days To Deadline', compute='_compute_days')
    bid_ids = fields.One2many('tender.bid', 'tender_id', string="Bids")
    bid_count = fields.Integer(string='Bid Count', compute='_compute_bid_count')
    tender_management_line_ids=fields.One2many('tender.management.line','tender_management_id',string='Tender Management Line')

    @api.depends('date_created', 'date_bid_to_end')
    def _compute_days(self):
        for rec in self:
            today = date.today()
            if rec.date_bid_to_end:
                days_difference = (rec.date_bid_to_end - today).days
                rec.days_to_deadline = days_difference
            else:
                rec.days_to_deadline = 0
    @api.depends('bid_ids')
    def _compute_bid_count(self):
        for tender in self:
            tender.bid_count = len(tender.bid_ids)
    def action_approve(self):
       for rec in self:
           rec.state = 'approve'
    def action_done(self):
       for rec in self:
           rec.state = 'done'
    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'
    def action_draft(self):
        for rec in self:
            rec.state = 'draft'
    def action_approved(self):
        for rec in self:
            rec.state = 'approved'  
    def action_submit(self):
        for rec in self:
            rec.state = 'submit'

    @api.model
    def create(self, vals):
        if vals.get('ref', 'New') == 'New':
            vals['ref'] = self.env['ir.sequence'].next_by_code('tender.management') or 'New'
        return super(TenderManagement, self).create(vals)

    class TenderManagementLine(models.Model):
        _name='tender.management.line'
        _description = "Tender Management Line"

        product_id = fields.Many2one('product.product', string='Products')
        price_unit = fields.Float(string='Price')
        qty = fields.Integer(string='Quantity')
        tender_management_id=fields.Many2one('tender.management',string='Tender Management')


