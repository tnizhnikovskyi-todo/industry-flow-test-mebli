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
        infos = env['product.supplierinfo'].search([('partner_id', '=', vendor.id), ('date_end', '=', False)])
        self.assertEqual(len(infos), 2, "one valid line per product")
        history = env['product.supplierinfo'].search([('partner_id', '=', vendor.id), ('date_end', '!=', False)])
        self.assertEqual(history.price, 800.0, "the earlier price stays as a dated history line")
        board_info = infos.filtered(lambda i: i.product_tmpl_id == board.product_tmpl_id)
        self.assertEqual((board_info.price, board_info.delay), (845.5, 4))
        self.assertEqual(infos.filtered(lambda i: i.product_tmpl_id == hinge.product_tmpl_id).price, 62.0)
        self.assertIn('ZZ-1', vendor.message_ids[:1].body)

    def _wizard(self, vendor, rows, filename='prices.csv', **vals):
        text = '\n'.join(';'.join(str(c) for c in row) for row in rows)
        return self.env['td.mebli.price.import'].create(dict(
            {'partner_id': vendor.id, 'filename': filename, 'file': base64.b64encode(text.encode())}, **vals))

    def test_numbers_written_by_people(self):
        from odoo.addons.td_mebli_purchase.wizard.price_import import to_number
        self.assertEqual(to_number('12 345,00 грн'), 12345.0)
        self.assertEqual(to_number('12 345,50 ₴'), 12345.5)
        self.assertEqual(to_number('1.234,56'), 1234.56)
        self.assertEqual(to_number('5 дн.'), 5.0)
        for text in ('за запитом', '5-7 днів', '', 'грн'):
            self.assertIsNone(to_number(text), text)

    def test_unhappy_rows_are_errors_not_zero(self):
        env = self.env
        vendor = env['res.partner'].create({'name': 'Fittings vendor'})
        board = env['product.product'].create({'name': 'Board Z', 'default_code': 'BZ', 'type': 'consu'})
        hinge = env['product.product'].create({'name': 'Hinge Z', 'default_code': 'HZ', 'type': 'consu'})
        rail = env['product.product'].create({'name': 'Rail Z', 'default_code': 'RZ', 'type': 'consu'})
        info = env['product.supplierinfo'].create({'partner_id': vendor.id, 'product_tmpl_id': hinge.product_tmpl_id.id,
                                                   'price': 60.0, 'delay': 6})
        wizard = self._wizard(vendor, [
            ['Артикул', 'Найменування', 'Ціна, грн', 'Строк'],
            ['', 'Плити ДСП', '', ''],                      # a section header: skipped
            ['BZ', 'Board Z', '12 345,00 грн', '5 дн.'],     # recognized with the units
            ['HZ', 'Hinge Z', '64,00', '5-7 днів'],          # price written, the lead time kept
            ['RZ', 'Rail Z', 'за запитом', '3'],             # error: not written, not a zero price
        ])
        wizard.action_recognize()
        lines = {l.code: l for l in wizard.line_ids}
        self.assertEqual(set(lines), {'BZ', 'HZ', 'RZ'})
        self.assertEqual((lines['BZ'].status, lines['BZ'].price, lines['BZ'].delay), ('new', 12345.0, 5))
        self.assertEqual(lines['HZ'].status, 'update')
        self.assertFalse(lines['HZ'].has_delay)
        self.assertIn('5-7', lines['HZ'].error)
        self.assertEqual(lines['RZ'].status, 'error')
        self.assertIn('за запитом', lines['RZ'].error)
        self.assertEqual((wizard.change_count, wizard.error_count), (2, 1), "the errors are counted before writing")
        wizard.action_import()
        infos = env['product.supplierinfo'].search([('partner_id', '=', vendor.id)])
        self.assertFalse(infos.filtered(lambda i: i.product_tmpl_id == rail.product_tmpl_id), "an error is not written")
        self.assertFalse(infos.filtered(lambda i: i.price == 0.0))
        hinge_now = infos.filtered(lambda i: i.product_tmpl_id == hinge.product_tmpl_id and not i.date_end)
        self.assertEqual((hinge_now.price, hinge_now.delay), (64.0, 6), "the lead time not recognized is not overwritten")
        self.assertEqual(infos.filtered(lambda i: i.product_tmpl_id == board.product_tmpl_id).price, 12345.0)
        self.assertIn('RZ', vendor.message_ids[:1].body)
        self.assertTrue(info.exists())

    def test_new_prices_keep_the_history(self):
        env = self.env
        vendor = env['res.partner'].create({'name': 'Dated vendor'})
        board = env['product.product'].create({'name': 'Board D', 'default_code': 'BD', 'type': 'consu'})
        old = env['product.supplierinfo'].create({'partner_id': vendor.id, 'product_tmpl_id': board.product_tmpl_id.id,
                                                  'price': 800.0, 'delay': 5, 'date_start': '2026-01-01'})
        expired = env['product.supplierinfo'].create({'partner_id': vendor.id, 'product_tmpl_id': board.product_tmpl_id.id,
                                                      'price': 700.0, 'date_start': '2025-01-01', 'date_end': '2025-12-31'})
        wizard = self._wizard(vendor, [['Артикул', 'Ціна'], ['BD', '845,50']], date_start='2026-11-01')
        wizard.action_recognize()
        self.assertEqual((wizard.line_ids.status, wizard.line_ids.supplierinfo_id), ('update', old))
        wizard.action_import()
        self.assertEqual((old.price, str(old.date_start), str(old.date_end)), (800.0, '2026-01-01', '2026-10-31'),
                         "the earlier price stays as history")
        self.assertEqual((expired.price, str(expired.date_end)), (700.0, '2025-12-31'), "an expired line is not touched")
        new = env['product.supplierinfo'].search([('partner_id', '=', vendor.id), ('date_start', '=', '2026-11-01')])
        self.assertEqual((new.price, new.delay), (845.5, 5))
        # the same date again: the dated line is corrected, not duplicated
        wizard = self._wizard(vendor, [['Артикул', 'Ціна'], ['BD', '850']], date_start='2026-11-01')
        wizard.action_recognize()
        wizard.action_import()
        self.assertEqual(new.price, 850.0)
        self.assertEqual(env['product.supplierinfo'].search_count([('partner_id', '=', vendor.id)]), 3)

    def test_d06_buyer_imports_the_price_list(self):
        """D-06 (AC-087, tr/security.md §1): the buyer (Purchase: User, no Purchase manager / Product manager) imports
        the price list of the supplier: the vendor pricelist lines are created and the earlier price is closed."""
        env = self.env
        buyer = env['res.users'].create({
            'name': 'Buyer', 'login': 'td_d06_buyer', 'email': 'td_d06_buyer@example.com',
            'group_ids': [(6, 0, [env.ref('base.group_user').id, env.ref('purchase.group_purchase_user').id])]})
        self.assertFalse(buyer.has_group('purchase.group_purchase_manager'))
        self.assertFalse(buyer.has_group('product.group_product_manager'))
        vendor = env['res.partner'].create({'name': 'Fittings vendor'})
        hinge = env['product.product'].create({'name': 'Hinge Z', 'default_code': 'HZ-1', 'type': 'consu'})
        env['product.supplierinfo'].create({'partner_id': vendor.id, 'product_tmpl_id': hinge.product_tmpl_id.id,
                                            'price': 50.0, 'date_start': '2026-01-01'})
        text = 'Артикул;Найменування;Ціна\nHZ-1;Hinge Z;55,00'
        wizard = env['td.mebli.price.import'].with_user(buyer).create({
            'partner_id': vendor.id, 'filename': 'prices.csv', 'file': base64.b64encode(text.encode())})
        wizard.action_recognize()
        self.assertEqual(wizard.line_ids.mapped('status'), ['update'])
        wizard.action_import()
        infos = env['product.supplierinfo'].search([('partner_id', '=', vendor.id)], order='id')
        self.assertEqual(infos.mapped('price'), [50.0, 55.0])
        self.assertTrue(infos[0].date_end, "the earlier price is closed as history")
