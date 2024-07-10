{
    'name': 'Hospital Management',
    'Version': '1.0.0',
    'sequence': -100,
    'author': 'Mark',
    'category': 'Hospital',
    'summary': 'Hospital management system',
    'description': """Hospital management system""",
    'depends': ['mail', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/patient_view.xml',
        'views/female_patient_view.xml',
        'views/appointment_view.xml',
    ],
    'demo': [],
    'auto-install': False,
    'application': True,
    'license': 'LGPL-3',
}
