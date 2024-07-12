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
        'views/patient_view.xml',
        'views/female_patient_view.xml',
        'views/appointment_view.xml',
        'views/patient_tag_view.xml',
    ],
    'demo': [],
    'auto-install': False,
    'application': True,
    'license': 'LGPL-3',
}