{
    'name': 'ToDo Mebli: notifications, letters to the customer, morning briefing',
    'summary': 'Activity for the salesperson when the forecast date passes the promised one, letters to the customer '
               '(installation, payment, new date) and a morning briefing of the owner — standard activities, mail '
               'templates and scheduled actions.',
    'description': 'Positions 1, 2 and 32 of the furniture package (F-50, F-51, F-64). Everything is the standard '
                   'messaging of Odoo 19 Community: mail.activity on the order (created when the forecast date passes the '
                   'promised one, closed when it comes back, never twice), mail.template letters posted in the chatter '
                   'of the record and queued for sending, scheduled actions (ir.cron). The briefing is a template filled '
                   'from the data of the package by fixed rules, no AI. No SMS and no external services.',
    'version': '19.0.1.1.2',
    'category': 'Sales/Sales',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_dashboard'],
    'data': [
        'data/mail_activity_type_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
}
