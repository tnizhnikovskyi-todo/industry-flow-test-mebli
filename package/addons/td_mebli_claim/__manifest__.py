{
    'name': 'ToDo Mebli: claims',
    'summary': 'A claim of the customer on the standard repair order: the order and the part it concerns, the photo and '
               'the remake in production; the reason and who pays are the standard tags and «Under Warranty».',
    'description': 'Screen S-14 of the furniture package on Odoo 19 Community: the stages, parts and dates are the '
                   'standard Repairs app (the reason is a standard tag, the factory pays when the repair is under '
                   'warranty); this module links the repair to the furniture order and its part.',
    'version': '19.0.1.1.1',
    'category': 'Manufacturing/Repair',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_base', 'td_mebli_sale', 'td_mebli_install', 'repair'],
    'data': [
        'data/product_data.xml',
        'views/repair_views.xml',
    ],
    'installable': True,
}
