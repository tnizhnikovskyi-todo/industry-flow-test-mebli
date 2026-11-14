{
    'name': 'ToDo Mebli: exchange with BAS/BAF',
    'summary': 'Exchange of the furniture package with the accounting of the customer in BAS/BAF: invoices, purchases, '
               'payments, accruals and the time sheet in batches with a log.',
    'description': 'F-47, F-41, F-61 of the furniture package (AC-039…AC-042, AC-078, AC-109; tr/integrations.md §1). '
                   'Our side of the exchange: channels per company, batches with the file of the batch, the log of '
                   'each document, the external codes of BAS on partners, products and employees, the status «Sent to '
                   'BAS» that locks the document (corrections only by a reversal). The format of BAS is not agreed yet '
                   '(ВП-1): the batch is a JSON file of our draft schema (transport «file»); the HTTP transport is a '
                   'stub until the contract.',
    'version': '19.0.1.1.3',
    'category': 'Accounting/Accounting',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_install', 'td_mebli_attendance', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'security/td_mebli_bas_security.xml',
        'data/td_mebli_bas_data.xml',
        'views/bas_views.xml',
        'views/document_views.xml',
    ],
    'installable': True,
}
