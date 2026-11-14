{
    'name': 'ToDo Mebli: bridge to Planning (Enterprise)',
    'summary': (
        'Bridge of the furniture package to Planning (Enterprise): the crews of an installation visit get '
        'Planning shifts (Gantt) linked to the task.'),
    'description': 'AC-128 (F-38, box C, tr/ee-bridges.md). Installs by itself (auto_install) on Odoo Enterprise when '
                   'both td_mebli_install and planning are installed; on Community it is never installed. NOT VERIFIED on '
                   'Enterprise: the fields and methods of the Enterprise models are assumptions until the access to '
                   'Odoo 19 Enterprise (ВП-4); the tests of this module run only there.',
    'version': '19.0.1.1.1',
    'category': 'Hidden',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_install', 'planning'],
    'data': ['security/td_mebli_bridge_security.xml', 'data/hide_td_screens.xml', 'views/bridge_views.xml'],
    'auto_install': True,
    'installable': True,
}
