{
    'name': 'ToDo Mebli: bridge to Sign (Enterprise)',
    'summary': (
        'Bridge of the furniture package to Sign (Enterprise): the contract and the installation act go as '
        'Sign requests with the PDF of our templates; the signed file comes back to the chatter of the order '
        'or the act.'),
    'description': 'AC-129 (F-43, box C, tr/ee-bridges.md). Installs by itself (auto_install) on Odoo Enterprise when '
                   'both td_mebli_install and sign are installed; on Community it is never installed. NOT VERIFIED on '
                   'Enterprise: the fields and methods of the Enterprise models are assumptions until the access to '
                   'Odoo 19 Enterprise (ВП-4); the tests of this module run only there.',
    'version': '19.0.1.1.0',
    'category': 'Hidden',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_install', 'sign'],
    'data': ['views/bridge_views.xml'],
    'auto_install': True,
    'installable': True,
}
