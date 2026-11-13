{
    'name': 'ToDo Mebli: order cost plan vs actual',
    'summary': 'Plan and actual cost and margin of every furniture order: materials and hours of its manufacturing orders.',
    'description': 'Screen S-11 of the furniture package. The plan is the standard cost of the order lines (sale_margin); '
                   'the actual is read from the finished manufacturing orders the same way the standard MO Overview '
                   'reads it: consumed components at their cost and the real hours of the work orders at the hourly '
                   'cost of the work center. Nothing is entered here. Idea of REUSE-01 (td_sale_cost), written anew for '
                   'Community without the 3D-print articles.',
    'version': '19.0.1.1.1',
    'category': 'Sales/Sales',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_base', 'td_mebli_sale', 'td_mebli_cutting', 'td_mebli_install'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
}
