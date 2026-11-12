{
    'name': 'ToDo Mebli: measurement sheet',
    'summary': 'Measurement sheet of the furniture order: niches, appliances of the customer, photos and the check «does not fit».',
    'description': 'Screen S-15 of the furniture package. The request and the visit are the standard CRM opportunity and '
                   'calendar meeting; this module keeps only what the standard has no place for: the niches, the '
                   'appliances of the customer and their sizes, and checks that every appliance fits its niche.',
    'version': '19.0.1.0.0',
    'category': 'Sales/CRM',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_sale', 'sale_crm'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence_data.xml',
        'views/measure_views.xml',
    ],
    'installable': True,
}
