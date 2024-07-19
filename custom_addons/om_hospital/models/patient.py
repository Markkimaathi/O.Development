from odoo import api, fields, models
from _datetime import date


class HospitalPatient(models.Model):
    _name = "hospital.patient"
    _description = "Hospital Patient"
    _inherit = ['mail.thread', 'mail.activity.mixin',]

    name = fields.Char(string="Name", tracking=True)
    ref = fields.Char(string="Reference", readonly=True, copy=False, default='New')
    date_of_birth = fields.Date(string='Date Of Birth')
    age = fields.Integer(string="Age", compute='_compute_age', tracking=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender", tracking=True)
    active = fields.Boolean(string="Active", default=True)

    @api.depends('date_of_birth')
    def _compute_age(self):
        for rec in self:
            today = date.today()
            if rec.date_of_birth:
               rec.age = today.year - rec.date_of_birth.year
            else:
               rec.age = 0

    @api.model
    def create(self, vals):
        if vals.get('ref', 'New') == 'New':
            vals['ref'] = self.env['ir.sequence'].next_by_code('hospital.patient') or 'New'
        return super(HospitalPatient, self).create(vals)
