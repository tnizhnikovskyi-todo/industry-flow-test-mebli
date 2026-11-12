{
    'name': 'ToDo Mebli: configurator, price and planned cost',
    'summary': 'Furniture dimensions in the sales configurator, size-based price, order BoM and planned margin',
    'version': '19.0.1.0.0',
    'category': 'Sales/Sales',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_mrp', 'sale_mrp', 'sale_margin', 'sale_purchase_stock', 'purchase_mrp'],
    'data': [
        'security/ir.model.access.csv',
        'security/purchase_security.xml',
        'views/sale_order_views.xml',
        'views/mrp_bom_views.xml',
        'views/order_cost_report_views.xml',
        'views/sale_order_dates_views.xml',
        'views/order_change_views.xml',
        'views/payment_term_views.xml',
        'report/contract_report.xml',
    ],
    'assets': {
        'web.assets_tests': [
            'td_mebli_sale/static/tests/tours/**/*',
        ],
    },
    'installable': True,
    'application': False,
}
