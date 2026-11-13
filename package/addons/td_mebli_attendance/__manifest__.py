{
    'name': 'ToDo Mebli: shop floor time sheet for BAS',
    'summary': 'Standard Attendances in the kiosk with a PIN for the workers of the shop floor and the export of the '
               'monthly time sheet in a file for BAS (imitation of the exchange).',
    'description': 'Position 23 of the furniture package (F-61). The check-in and check-out with a PIN in the kiosk are '
                   'the standard Attendances of Odoo 19 Community (hr_attendance, kiosk mode with PIN). This module only '
                   'adds the export of the time sheet (employee, days, hours) into a CSV file for the payroll in BAS; the '
                   'exchange with BAS itself is not in the package slice: the file is marked «imitation».',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Attendances',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/timesheet_export_views.xml',
    ],
    'installable': True,
}
