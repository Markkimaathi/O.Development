{
    "name": "Create Purchase from Lead/Pipeline",
    "version": "17.0.0.1",
    "category": 'CRM',
    "summary": "Create purchase order form lead opportunity request for quotation pipeline to purchase order crm lead opportunity lead to purchase pipeline opportunity create rfq from lead and pipeline lead/pipeline product to rfq/po create request for quotation pipeline",
    "description": """Create RFQ/PO from Lead/Pipeline odoo app allows you to easily convert a lead or pipeline opportunity into a request for quotation (RFQ) or purchase order (PO) with just a few clicks. With this app, user can add products to lead and then quickly convert that into RFQs or POs with the scheduled date. also can access created purchase order from the smart button on lead and, the lead will be linked with the purchase order.""",
    'author': 'BrowseInfo',
    'website': 'https://www.browseinfo.com',
    "depends": [
        'crm','purchase'
    ],
    "data": [
        'security/ir.model.access.csv',
        'wizard/purachse_order_wizard_view.xml',
        'views/crm_lead_inherit_views.xml',
        'views/purchase_order_view.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    'live_test_url':'https://youtu.be/oHOfUopDr5c',
    "images":["static/description/Create-Purchase-from-Lead-Pipeline-Banner.gif"],
}
