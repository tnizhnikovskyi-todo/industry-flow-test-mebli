{
    'name': 'ToDo Mebli: manager dashboard',
    'summary': 'One-screen dashboard for the owner of a furniture factory: the KPIs of the A box (BOX §11.1), every card opens the records it counted.',
    'description': 'A client action on Odoo 19 Community (no Enterprise, no spreadsheet): the figures are read from the sales, '
                   'manufacturing and cutting data of the furniture package. Responsive: the same screen works on a phone.',
    'version': '19.0.1.1.0',
    'category': 'Manufacturing/Manufacturing',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_base', 'td_mebli_cutting', 'td_mebli_measure', 'td_mebli_install', 'td_mebli_claim', 'td_mebli_cost', 'td_mebli_purchase'],
    'data': [
        'security/security.xml',
        'views/dashboard_views.xml',
        'views/sale_order_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'td_mebli_dashboard/static/src/**/*',
        ],
    },
    'installable': True,
    'application': True,
}
