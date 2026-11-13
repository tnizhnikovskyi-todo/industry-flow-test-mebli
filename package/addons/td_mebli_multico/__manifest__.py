{
    'name': 'ToDo Mebli: installation by another legal entity',
    'summary': 'One seller per order; the installation by another legal entity (a sole proprietor) is a separate '
               'service order of that company, linked to the main order (box B, VP-03 multi_install_fop).',
    'description': 'F-25 by the rule AI-14 (tr/td_mebli_multico.md): the salesperson marks «Installation by» on the '
                   'order of the seller; the confirmation moves the installation line to a new service order of the '
                   'installing company (its own project task), the lines of the main order are not split. Standard '
                   'multi-company of Odoo 19 Community; there are no inter-company rules in CE.',
    'version': '19.0.1.1.1',
    'category': 'Sales/Sales',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_install'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
}
