{
    'name': 'ToDo Mebli: supplier prices against history',
    'summary': 'Purchase lines whose price is above the average of the earlier purchases of the same product.',
    'description': 'Part of screen S-08 of the furniture package. Purchases, vendor price lists, shortage and MTO '
                   'purchases are standard (purchase_stock); this module only compares the price of a purchase line with '
                   'the average price of the confirmed purchases of the same product over the previous 180 days. The price list of a '
                   'supplier from Excel or CSV is written into the standard vendor pricelist (product.supplierinfo).',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Purchase',
    'license': 'LGPL-3',
    'author': 'ToDo',
    'depends': ['purchase_stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_views.xml',
        'wizard/price_import_views.xml',
    ],
    'installable': True,
}
