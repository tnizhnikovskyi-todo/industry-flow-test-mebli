{
    'name': 'ToDo Mebli: manager dashboard',
    'summary': 'One-screen dashboard for the owner of a furniture factory: revenue, margin, load, launch time, cutting waste, plan vs actual.',
    'description': 'A client action on Odoo 19 Community (no Enterprise, no spreadsheet): the figures are read from the sales, '
                   'manufacturing and cutting data of the furniture package. Responsive: the same screen works on a phone.',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing/Manufacturing',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_sale', 'td_mebli_cutting'],
    'data': [
        'security/security.xml',
        'views/dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'td_mebli_dashboard/static/src/**/*',
        ],
    },
    'installable': True,
    'application': True,
}
