{
    'name': 'ToDo Mebli: base',
    'summary': 'Parameters of the furniture package on the company, feature groups of box B, PDF font with Cyrillic.',
    'description': 'Common base of the furniture package td_mebli_*: the answers of the questionnaire (VP-xx of SPEC §11) '
                   'as fields of the company, the warranty term of a product category, the groups «Finance» and «Sees '
                   'the margin», the feature groups of box B (VP-02) as visibility flags of menus and buttons, the '
                   'font of the package reports with the full Cyrillic set. The post-init hook moves the system '
                   'parameters of the slice into the fields of the company.',
    'version': '19.0.1.1.2',
    'category': 'Manufacturing/Manufacturing',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['base_setup', 'account', 'sales_team'],
    'data': [
        'security/td_mebli_security.xml',
        'views/res_config_settings_views.xml',
        'views/product_category_views.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'td_mebli_base/static/src/scss/td_mebli_report.scss',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
}
