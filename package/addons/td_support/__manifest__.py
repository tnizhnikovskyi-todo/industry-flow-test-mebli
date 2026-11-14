{
    'name': 'ToDo: Support',
    'summary': 'Support request to ToDo from the systray and from the error dialogs of Odoo.',
    'description': 'Community and Enterprise: the «ToDo Support» icon in the systray opens a request form (subject, '
                   'description, attachments or a screenshot, contact, consent); the request is kept in the database '
                   'and sent to the ToDo support by the outgoing mail server. The error dialogs of Odoo get the '
                   'button '
                   '«Send to ToDo Support» with the traceback, the URL, the version of Odoo, the td_* modules, the login '
                   'and the uuid of the database, shown to the user before sending. Passwords, tokens and cookies are '
                   'removed, sizes are limited, repeated sending is limited.',
    'version': '19.0.1.0.0',
    'category': 'Hidden/Tools',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['base_setup', 'mail'],
    'data': [
        'security/td_support_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/td_support_request_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'td_support/static/src/**/*',
        ],
        'web.assets_tests': [
            'td_support/static/tests/tours/**/*',
        ],
    },
    'installable': True,
}
