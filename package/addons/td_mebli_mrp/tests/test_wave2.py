import base64
import io

from odoo.tests import tagged

from .common import TdMebliCommon


def _xlsx(rows):
    import openpyxl
    book = openpyxl.Workbook()
    for row in rows:
        book.active.append(row)
    buffer = io.BytesIO()
    book.save(buffer)
    return base64.b64encode(buffer.getvalue())


@tagged('post_install', '-at_install')
class TestWave2Mrp(TdMebliCommon):
    """F-52 overconsumption warning, F-01/position 4 Excel import, F-57 analogs."""

    def test_order_bom_warns_about_overconsumption(self):
        bom = self.env['mrp.bom']._td_generate_order_bom(self.cabinet, self.dims, self.selections)
        self.assertEqual(bom.consumption, 'warning', "standard «Allowed with warning» (mrp_bom.py consumption)")

    def test_excel_file_is_imported_like_csv(self):
        bom = self.env['mrp.bom'].create({'product_tmpl_id': self.cabinet_tmpl.id,
                                          'bom_line_ids': [(0, 0, {'product_id': self.board_a.id, 'product_qty': 1})]})
        data = _xlsx([['Деталь', 'Довжина', 'Ширина', 'К-сть', 'Матеріал'],
                      ['Боковина', 720, 560, 2, 'Board A'], ['Полиця', 564.0, 540, 1, None]])
        wizard = self.env['td.mebli.spec.import'].create({'bom_id': bom.id, 'filename': 'kitchen.xlsx', 'file': data})
        wizard.action_recognize()
        self.assertEqual(wizard.preview_count, 2)
        wizard.action_import()
        self.assertEqual(bom.td_part_ids.mapped('name'), ['Боковина', 'Полиця'])
        self.assertEqual(bom.td_part_ids[1].length_mm, 564)

    def test_short_board_suggests_and_uses_the_analog(self):
        analog = self.env['product.product'].create({'name': 'Board A2', 'is_storable': True,
                                                     'uom_id': self.board_a.uom_id.id})
        self.board_a.product_tmpl_id.td_analog_ids = [(6, 0, analog.ids)]
        stock = self.env.ref('stock.stock_location_stock')
        self.env['stock.quant']._update_available_quantity(analog, stock, 100.0)
        bom = self.env['mrp.bom']._td_generate_order_bom(self.cabinet, self.dims, self.selections)
        production = self.env['mrp.production'].create({'product_id': self.cabinet.id, 'bom_id': bom.id, 'product_qty': 1})
        production.action_confirm()
        move = production.move_raw_ids.filtered(lambda m: m.product_id == self.board_a)
        self.assertEqual(move.td_analog_id, analog, "board A is not in stock, the analog is")
        self.assertIn('Board A2', move.td_analog_hint)
        move.action_td_use_analog()
        self.assertEqual(move.product_uom_qty, 0.0)
        self.assertIn(analog, production.move_raw_ids.product_id)
        self.assertIn(analog, bom.td_part_ids.material_id)
        self.assertNotIn(self.board_a, bom.td_part_ids.material_id)
