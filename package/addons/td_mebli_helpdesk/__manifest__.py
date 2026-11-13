{
    'name': 'ToDo Mebli: bridge to Helpdesk (Enterprise)',
    'summary': (
        'Bridge of the furniture package to Helpdesk (Enterprise): the ticket is linked to the order, the '
        'part and the claim; the remake is started from the ticket; the claim kanban of td_mebli_claim is '
        'hidden.'),
    'description': 'AC-113 (F-17, box C, tr/ee-bridges.md). Installs by itself (auto_install) on Odoo Enterprise when '
                   'both td_mebli_claim and helpdesk are installed; on Community it is never installed. NOT VERIFIED on '
                   'Enterprise: the fields and methods of the Enterprise models are assumptions until the access to '
                   'Odoo 19 Enterprise (ВП-4); the tests of this module run only there.',
    'version': '19.0.1.1.0',
    'category': 'Hidden',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_claim', 'helpdesk'],
    'data': ['security/td_mebli_bridge_security.xml', 'data/hide_td_screens.xml', 'views/bridge_views.xml'],
    'auto_install': True,
    'installable': True,
}
