{
    'name': 'ToDo Mebli: data migration',
    'summary': 'Import order of the master data templates of the package and the reconciliation report of the migration '
               '(prepayments of open orders, number of open orders, stock) against the source.',
    'description': 'F-46 of the furniture package (AC-089, AC-090; tr/migration.md §3). The steps of the import follow the '
                   'CSV templates of A-13 (package/master-data/README.md) and open the standard import of Odoo; the '
                   'templates themselves are not copied here. The reconciliation compares the values of the source with '
                   'Odoo and is «reconciled» only with a zero difference or with an explanation signed by a manager. '
                   'The converters scripts/convert_bas.py and scripts/convert_bazis.py are command-line skeletons for '
                   'B-06: the export formats of BAS/BAF and BAZIS are not known yet (ВП-1, ВП-3).',
    'version': '19.0.1.1.6',
    'category': 'Sales/Sales',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['td_mebli_sale', 'sale_stock', 'base_import'],
    'data': [
        'security/ir.model.access.csv',
        'security/td_mebli_migration_security.xml',
        'data/td_mebli_migration_step_data.xml',
        'views/migration_views.xml',
    ],
    'installable': True,
}
