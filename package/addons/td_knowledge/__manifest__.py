{
    'name': 'ToDo: Knowledge Base',
    'summary': 'Knowledge base for the whole system: articles in sections and help for the current screen.',
    'description': 'Community and Enterprise: articles with sections, search, attachments and the Odoo editor; '
                   'an article can be linked to models (screens) and applications, and the «Help» icon in the top bar '
                   'shows the articles of the current screen and lets an editor add one. Editors write, every internal '
                   'user reads; an article can be limited to groups. Articles shipped by a package are not '
                   'overwritten by an update. Written from scratch (not the Enterprise Knowledge app, not OCA).',
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['mail'],
    'data': [
        'security/td_knowledge_security.xml',
        'security/ir.model.access.csv',
        'views/td_knowledge_article_views.xml',
        'data/td_knowledge_article_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'td_knowledge/static/src/**/*',
        ],
        'web.assets_tests': [
            'td_knowledge/static/tests/tours/**/*',
        ],
    },
    'application': True,
    'installable': True,
}
