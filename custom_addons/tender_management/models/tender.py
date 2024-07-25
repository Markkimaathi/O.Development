from odoo import api, fields, models
from _datetime import date


class TenderManagement(models.Model):
    _name = "tender.management"
    _description = "Tender Management"
    _inherit = ['mail.thread', 'mail.activity.mixin',]

    name = fields.Char(string="Tender")
    ref = fields.Char(string="Reference", readonly=True, copy=False, default='New')
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