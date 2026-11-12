{
    'name': 'ToDo Mebli: claims',
    'summary': 'A claim of the customer on the standard repair order: the order and the part it concerns, the reason, '
               'who pays, the photo and the remake in production.',
    'description': 'Screen S-14 of the furniture package on Odoo 19 Community: the stages, parts and dates are the '
                   'standard Repairs app; this module links the repair to the furniture order and its part and keeps '
                   'the reason and the payer, which the standard has no field for.',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing/Repair',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_sale', 'repair'],
    'data': [
        'views/repair_views.xml',
    ],
    'installable': True,
}
