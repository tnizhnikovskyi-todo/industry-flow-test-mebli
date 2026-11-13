{
    'name': 'ToDo Mebli: NBU rate and BAS exchange status',
    'summary': 'Exchange rates of the National Bank of Ukraine into the standard currency rates; the status of the '
               'exchange of an order with BAS/BAF.',
    'description': 'F-26 and F-47 of the furniture package. Community has no automatic currency rates (the module for '
                   'live rates is not part of Community), so this module loads the official NBU rates into the standard '
                   'res.currency.rate. Online loading is off by default (system parameter td_mebli_ua.nbu_online); on '
                   'show databases the rates are loaded from a fixed table and marked as an imitation. The BAS/BAF '
                   'exchange itself is not part of the slice: the order only shows its status (imitation).',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_base', 'sale'],
    'data': [
        'data/ir_cron_data.xml',
        'views/views.xml',
    ],
    'installable': True,
}
