{
    'name': 'RFQ Test',
    'Version': '1.0.0',
    'sequence': -50,
    'author': 'Mark',
    'category': 'RFQ',
    'summary': 'Request For Quotation',
    'description': """RFQ""",
    'depends': ['mail', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        # 'views/purchase_request.xml',
    ],
    'demo': [],
    'auto-install': False,
    'application': True,
    'license': 'LGPL-3',
}