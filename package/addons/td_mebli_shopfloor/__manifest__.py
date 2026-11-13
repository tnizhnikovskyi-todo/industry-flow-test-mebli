{
    'name': 'ToDo Mebli: bridge to Shop Floor (Enterprise)',
    'summary': (
        'Bridge of the furniture package to Shop Floor (Enterprise): the work order shows the parts of the '
        'order; the tablet of td_mebli_shop is hidden.'),
    'description': 'AC-126 (F-32, box C, tr/ee-bridges.md). Installs by itself (auto_install) on Odoo Enterprise when '
                   'both td_mebli_shop and mrp_workorder are installed; on Community it is never installed. NOT VERIFIED on '
                   'Enterprise: the fields and methods of the Enterprise models are assumptions until the access to '
                   'Odoo 19 Enterprise (ВП-4); the tests of this module run only there.',
    'version': '19.0.1.1.0',
    'category': 'Hidden',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_shop', 'mrp_workorder'],
    'data': ['security/td_mebli_bridge_security.xml', 'data/hide_td_screens.xml', 'views/bridge_views.xml'],
    'post_init_hook': 'post_init_hook',
    'auto_install': True,
    'installable': True,
}
