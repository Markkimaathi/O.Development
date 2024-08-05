from odoo import models, fields

class Category(models.Model):
    _name = 'tender.category'
    _description = 'Category'

    category_name = fields.Char(string="Category Name")
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
