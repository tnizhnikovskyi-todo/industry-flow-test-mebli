{
    'name': 'ToDo Mebli: bridge to Field Service (Enterprise)',
    'summary': (
        'Bridge of the furniture package to Field Service (Enterprise): the installation act and the crew '
        'percent are linked to the Field Service task; the installation calendar of td_mebli_install is '
        'hidden.'),
    'description': 'AC-128 (F-38, box C, tr/ee-bridges.md). Installs by itself (auto_install) on Odoo Enterprise when '
                   'both td_mebli_install and industry_fsm are installed; on Community it is never installed. NOT VERIFIED on '
                   'Enterprise: the fields and methods of the Enterprise models are assumptions until the access to '
                   'Odoo 19 Enterprise (ВП-4); the tests of this module run only there.',
    'version': '19.0.1.1.1',
    'category': 'Hidden',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_install', 'industry_fsm'],
    'data': ['security/td_mebli_bridge_security.xml', 'data/hide_td_screens.xml'],
    'auto_install': True,
    'installable': True,
}
