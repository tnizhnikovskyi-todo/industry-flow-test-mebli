{
    'name': 'ToDo Mebli: installation acts and accruals',
    'summary': 'Installation visits on the standard project calendar, the act with photos, defects and the signature of '
               'the customer, the crew percent and the accruals of the shop and the crews.',
    'description': 'Screens S-12 and S-17 of the furniture package on Odoo 19 Community. A visit is a standard project '
                   'task of the order (calendar without Gantt: Gantt is Enterprise only); the act, its defects and the '
                   'photo archive flag are new. Accruals: piecework by the piece rate of the operation (per part, metre '
                   'of edge, m2 of board or per operation) for done work orders, shared by the time lines of the tablet, the crew percent from a signed final act, bonuses and '
                   'penalties with a reason. Payroll is Enterprise only and has no Ukrainian localisation: the accruals '
                   'are handed over to the accounting system of the customer.',
    'version': '19.0.1.1.3',
    'category': 'Services/Project',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_base', 'td_mebli_shop', 'sale_project'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence_data.xml',
        'views/act_views.xml',
        'views/accrual_views.xml',
        'views/payment_views.xml',
        'report/act_report.xml',
        'report/accrual_report.xml',
        'views/day_plan_views.xml',
    ],
    'installable': True,
}
