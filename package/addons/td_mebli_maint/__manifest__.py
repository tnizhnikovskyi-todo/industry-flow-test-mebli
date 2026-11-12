{
    'name': 'ToDo Mebli: maintenance of the machines',
    'summary': 'Standard Maintenance (Community) linked to the work centers of the shop floor: planned maintenance, '
               'breakdown requests and the downtime in the standard loss reasons of the section.',
    'description': 'Position 22 of the furniture package (F-60). Equipment, preventive and corrective requests are the '
                   'standard Maintenance of Odoo 19 Community. The link of a machine to its work center (Enterprise has it '
                   'in mrp_maintenance, Community does not) and the downtime of a breakdown written as a standard time '
                   'log of the work center with the standard loss reason «Equipment Failure».',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing/Maintenance',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['maintenance', 'mrp'],
    'data': [
        'views/maintenance_views.xml',
    ],
    'installable': True,
}
