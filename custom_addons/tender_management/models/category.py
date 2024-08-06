from odoo import models, fields

class Category(models.Model):
    _name = 'tender.category'
    _description = 'Category'

    name = fields.Char(string='Category Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)

