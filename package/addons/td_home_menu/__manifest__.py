{
    'name': 'ToDo: Home Menu',
    'summary': 'Home screen with application tiles for Odoo Community: search, keyboard, mobile.',
    'description': 'Community only: a home screen with the tiles of the root menus (web_icon), search of an '
                   'application by name and keyboard navigation; it opens from the navbar button and after the login. '
                   'Written from scratch on OWL. If web_enterprise is installed, the module changes nothing.',
    'version': '19.0.1.0.2',
    'category': 'Hidden/Tools',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'td_home_menu/static/src/**/*',
        ],
        'web.assets_tests': [
            'td_home_menu/static/tests/tours/**/*',
        ],
    },
    'installable': True,
}
