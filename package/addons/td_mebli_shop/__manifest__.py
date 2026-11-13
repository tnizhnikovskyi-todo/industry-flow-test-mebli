{
    'name': 'ToDo Mebli: shop floor tablet and packing list',
    'summary': 'Shop floor tablet with a PIN of the worker, quality step with a photo, packing list that does not let an '
               'incomplete set leave the warehouse.',
    'description': 'Screens S-06 and S-16 of the furniture package on Odoo 19 Community. The work orders, their timer and '
                   'the pause reasons are standard (mrp); in Community the time is written to the user of Odoo, so one '
                   'shared tablet user records the time and this module adds the worker who confirmed with the PIN of '
                   'the standard employee. Quality steps (Quality is Enterprise only) and the packing list by places '
                   'are new.',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing/Manufacturing',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_sale', 'hr_hourly_cost', 'sale_stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/kiosk_views.xml',
        'views/shop_views.xml',
        'views/kit_views.xml',
        'report/kit_report.xml',
        'report/label_report.xml',
    ],
    'installable': True,
}
