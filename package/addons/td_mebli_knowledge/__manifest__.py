{
    'name': 'ToDo Mebli: knowledge base articles',
    'summary': 'Starter articles of the furniture package in the knowledge base, linked to its screens.',
    'description': 'Installed automatically with td_knowledge and the furniture package: a section «Furniture: how we '
                   'work» with articles for the order, the measurement, the cutting, the installation act and the '
                   'claim, each linked to its screen. The articles are data with noupdate: the customer edits them, '
                   'an update of the package does not overwrite the edits.',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing/Manufacturing',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_knowledge', 'td_mebli_base'],
    'data': ['data/td_knowledge_article_data.xml'],
    'auto_install': True,
    'installable': True,
}
