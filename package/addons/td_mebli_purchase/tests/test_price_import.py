import base64
import io

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPriceImport(TransactionCase):
    """Position 19 (F-59): the price list of a supplier from Excel into the standard vendor pricelist."""

    def test_prices_go_to_the_vendor_pricelist(self):
        import openpyxl
        env = self.env
        vendor = env['res.partner'].create({'name': 'Board vendor'})
        board = env['product.product'].create({'name': 'Board X', 'default_code': 'BX-16', 'type': 'consu'})
        hinge = env['product.product'].create({'name': 'Hinge Y', 'default_code': 'HY', 'type': 'consu'})
        env['product.supplierinfo'].create({'partner_id': vendor.id, 'product_tmpl_id': board.product_tmpl_id.id,
                                            'price': 800.0, 'delay': 5})
        book = openpyxl.Workbook()
        for row in (['Артикул', 'Найменування', 'Ціна, грн', 'Строк, днів'], ['BX-16', 'Board X', '845,50', 4],
                    ['HY', 'Hinge Y', 62, 3], ['ZZ-1', 'Unknown', 10, 1]):
            book.active.append(row)
        buffer = io.BytesIO()
        book.save(buffer)
        wizard = env['td.mebli.price.import'].create({'partner_id': vendor.id, 'filename': 'prices.xlsx',
                                                      'file': base64.b64encode(buffer.getvalue())})
        wizard.action_recognize()
        self.assertEqual(wizard.line_ids.mapped('status'), ['update', 'new', 'unknown'])
        self.assertEqual((wizard.change_count, wizard.unknown_count), (2, 1))
        wizard.action_import()
        infos = env['product.supplierinfo'].search([('partner_id', '=', vendor.id)])
        self.assertEqual(len(infos), 2, "updated, not duplicated")
        board_info = infos.filtered(lambda i: i.product_tmpl_id == board.product_tmpl_id)
        self.assertEqual((board_info.price, board_info.delay), (845.5, 4))
        self.assertEqual(infos.filtered(lambda i: i.product_tmpl_id == hinge.product_tmpl_id).price, 62.0)
        self.assertIn('ZZ-1', vendor.message_ids[:1].body)
