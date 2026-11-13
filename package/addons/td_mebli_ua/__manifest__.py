{
    'name': 'ToDo Mebli: NBU rate',
    'summary': 'Exchange rates of the National Bank of Ukraine into the standard currency rates; prices of the '
               'quotations updated at the rate.',
    'description': 'F-26 and F-47 of the furniture package. Community has no automatic currency rates (the module for '
                   'live rates is not part of Community), so this module loads the official NBU rates into the standard '
                   'res.currency.rate. Online loading is off by default (system parameter td_mebli_ua.nbu_online); on '
                   'show databases the rates are loaded from a fixed table and marked as an imitation. A failed loading '
                   'leaves the rates as they are and gives the finance users an activity. The button «Update Prices '
                   'at the Rate» (feature group «nbu») recomputes only the quotations. The exchange with BAS/BAF is the '
                   'module td_mebli_bas.',
    'version': '19.0.1.1.1',
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
