from odoo import models, fields, api

class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = 'Purchase Request'

    name = fields.Char(string='Name', required=True)
    date_start = fields.Date(string='Start Date', required=True)
    requested_by = fields.Many2one('res.users', string='Requested By', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)
    origin = fields.Char(string='Origin')
    currency_id = fields.Many2one('res.currency', string='Currency')
    estimated_cost = fields.Monetary(string='Estimated Cost', currency_field='currency_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'To Approve'),
        ('approved', 'Approved'),
        ('done', 'Done'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', track_visibility='onchange')

    @api.depends('state')
    def _compute_message_needaction(self):
        for record in self:
            record.message_needaction = record.state == 'to_approve'

    message_needaction = fields.Boolean(string='Need Action', compute='_compute_message_needaction', store=True)

    @api.model
    def create(self, vals):
        record = super(PurchaseRequest, self).create(vals)
        if record.state == 'to_approve':
            record.message_post(body='Request for Quotation needs approval.')
        return record

    def write(self, vals):
        result = super(PurchaseRequest, self).write(vals)
        if 'state' in vals and vals['state'] == 'to_approve':
            self.message_post(body='Request for Quotation needs approval.')
        return result
