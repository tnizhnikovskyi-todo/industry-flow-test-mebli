{
    'name': 'ToDo Mebli: configurator, price and planned cost',
    'summary': 'Furniture dimensions in the sales configurator, size-based price, order BoM and planned margin',
    'version': '19.0.1.0.0',
    'category': 'Sales/Sales',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_mrp', 'sale_mrp', 'sale_margin'],
    'data': [
        'views/sale_order_views.xml',
        'views/mrp_bom_views.xml',
        'views/order_cost_report_views.xml',
    ],
    'assets': {
        'web.assets_tests': [
            'td_mebli_sale/static/tests/tours/**/*',
        ],
    },
    'installable': True,
    'application': False,
}
