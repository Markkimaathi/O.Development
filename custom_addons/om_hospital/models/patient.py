from datetime import date
from odoo import api, fields, models


class HospitalPatient(models.Model):
    _name = 'hospital.patient'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Hospital Patient'

    name = fields.Char(string='Name', tracking=True)
    date_of_birth = fields.Date(string='Date of Birth')
    ref = fields.Char(string='Reference', default='Mark')
    age = fields.Integer(string='Age', compute='_compute_age', tracking=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender', tracking=True,
                              default='female')
    active = fields.Boolean(string="Active", default=True)
    appointment_id = fields.Many2one('hospital.patient', string="Appointments")
    image = fields.Image(string="Image")
    tag_ids = fields.Many2many('patient.tag', string="Tags")

    @api.depends('date_of_birth')
    def _compute_age(self):
        for rec in self:
            today = date.today()
            if rec.date_of_birth:
                rec.age = today.year - rec.date_of_birth.year
            else:
                rec.age = 1