{
    'name': 'ToDo Mebli: bridge to Quality (Enterprise)',
    'summary': (
        'Bridge of the furniture package to Quality (Enterprise): quality points from the quality steps of '
        'the operations; the quality checks of td_mebli_shop are hidden; the dashboard reads the failed '
        'checks of Quality.'),
    'description': 'AC-127 (F-34, box C, tr/ee-bridges.md). Installs by itself (auto_install) on Odoo Enterprise when '
                   'both td_mebli_shop and quality_control are installed; on Community it is never installed. NOT VERIFIED on '
                   'Enterprise: the fields and methods of the Enterprise models are assumptions until the access to '
                   'Odoo 19 Enterprise (ВП-4); the tests of this module run only there.',
    'version': '19.0.1.1.0',
    'category': 'Hidden',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_shop', 'quality_control'],
    'data': ['security/td_mebli_bridge_security.xml', 'data/hide_td_screens.xml'],
    'post_init_hook': 'post_init_hook',
    'auto_install': True,
    'installable': True,
}
