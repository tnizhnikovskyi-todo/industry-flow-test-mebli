{
    'name': 'ToDo Mebli: shop floor time sheet for BAS',
    'summary': 'Standard Attendances in the kiosk with a PIN for the workers of the shop floor and the export of the '
               'monthly time sheet in a file for BAS (draft format of the exchange contract).',
    'description': 'Position 23 of the furniture package (F-61). The check-in and check-out with a PIN in the kiosk are '
                   'the standard Attendances of Odoo 19 Community (hr_attendance, kiosk mode with PIN). This module only '
                   'adds the export of the time sheet (employee, personnel code, days, hours, total) into a CSV file for '
                   'the payroll in BAS (AC-078); the module td_mebli_bas puts the file into an exchange batch.',
    'version': '19.0.1.1.0',
    'category': 'Human Resources/Attendances',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_base', 'hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/timesheet_export_views.xml',
    ],
    'installable': True,
}
