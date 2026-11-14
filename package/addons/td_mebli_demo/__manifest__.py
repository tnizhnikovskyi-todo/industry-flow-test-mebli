{
    'name': 'ToDo Mebli: demo catalog and stock',
    'summary': 'Showcase data for the furniture package: catalog, work centers, stock. Not for customers.',
    'description': 'Demo data of the furniture package (fictional brands). Installed only on show databases; '
                   'customers get the master data templates (A-13) instead.',
    'version': '19.0.1.1.2',
    'category': 'Manufacturing/Manufacturing',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_dashboard', 'td_mebli_ua', 'td_mebli_notify', 'td_mebli_maint', 'td_mebli_attendance', 'td_mebli_bas'],
    'data': [
        'data/settings_data.xml',
        'data/workcenter_data.xml',
        'data/material_data.xml',
        'data/attribute_data.xml',
        'data/product_data.xml',
        'data/partner_data.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
