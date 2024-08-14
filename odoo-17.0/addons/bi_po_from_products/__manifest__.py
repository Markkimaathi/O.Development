# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Create Purchase Order from Products',
    'version': '17.0.0.0',
    'category': 'Purchase',
    'summary': 'Create PO from products purchase order from product create request for quotation from products instant purchase orders from products quick RFQ form products directly for purchase order create multiple purchase form product create request for quotation',
    "description": """
       
        Create Purchase Order from Products Odoo App helps users to create the purchase order from the products by single click. User can select multiple products from list view of product variants, also can select vendor and create purchase order.

    """,
    'author': 'BrowseInfo',
    'website': 'https://www.browseinfo.com',
    'depends': ['base', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/view_purchaseorder_wizard.xml',
    ],
    'license':'OPL-1',
    'installable': True,
    'auto_install': False,
    'live_test_url':'https://youtu.be/V5tAq7J02QE',
    "images":['static/description/Purchase-Order-from-Products.gif'],
}
