# -*- coding: utf-8 -*-


{
    'name': 'Hospital Management ',
    'version': '1.0.0',
    'category': 'Hospital',
    'author': 'Joshua Mumo',
    'sequence': 1,
    'summary': 'Hospital management system',
    'description': """ Hospital management system """,
    'depends': ['mail'],
    'data': [
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/patient_views.xml',
        'views/female_patient_views.xml',
        'views/male_patient_views.xml',
        'views/gender_patient_views.xml',
        'views/appointment_views.xml',

    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
