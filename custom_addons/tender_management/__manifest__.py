# -*- coding: utf-8 -*-

{
    'name': 'Tender Management',
    'version': '1.0.0',
    'author': 'Joshua',
    'sequence': 50,
    'summary': 'Tender Management system',
    'description': """Tender Management system""",
    'depends': ['mail', 'product'],
    'data': [
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'security/tender_management_security.xml',
        'views/menu.xml',
        'views/tender_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
