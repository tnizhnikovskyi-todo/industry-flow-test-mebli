{
    'name': 'ToDo Mebli: knowledge base articles',
    'summary': 'Starter articles of the furniture package in the knowledge base, linked to its screens.',
    'description': 'Installed automatically with td_knowledge and the furniture package (its measurement, cutting, '
                   'installation and claim modules): a section «Furniture: how we work» with articles for the order, the measurement, the cutting, the installation act and the '
                   'claim, each linked to its screen. The articles are data with noupdate: the customer edits them, '
                   'an update of the package does not overwrite the edits.',
    'version': '19.0.1.1.1',
    'category': 'Manufacturing/Manufacturing',
    'license': 'LGPL-3',
    'author': 'ToDo',
    # the screens of the articles must exist when the data is loaded (model_ids search): A-14-5, A-11-fix2
    'depends': ['td_knowledge', 'td_mebli_base', 'td_mebli_measure', 'td_mebli_cutting', 'td_mebli_install',
                'td_mebli_claim'],
    'data': ['data/td_knowledge_article_data.xml'],
    'auto_install': True,
    'installable': True,
}
