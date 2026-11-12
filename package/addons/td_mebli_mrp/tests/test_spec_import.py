import base64

from odoo.tests import tagged

from .common import TdMebliCommon

CSV = "Деталь;Довжина;Ширина;К-сть;Матеріал;Кромка довж\nБоковина;720;560;2;Board A;1\nПолиця;564;540;1;;1\n"


@tagged('post_install', '-at_install')
class TestSpecImport(TdMebliCommon):

    def test_columns_are_recognized_by_their_titles(self):
        bom = self.env['mrp.bom'].create({'product_tmpl_id': self.cabinet_tmpl.id,
                                          'bom_line_ids': [(0, 0, {'product_id': self.board_a.id, 'product_qty': 1})]})
        wizard = self.env['td.mebli.spec.import'].create({'bom_id': bom.id, 'filename': 'kitchen.csv',
                                                          'file': base64.b64encode(CSV.encode())})
        wizard.action_recognize()
        self.assertEqual(wizard.preview_count, 2)
        self.assertIn('Довжина', wizard.mapping)
        wizard.action_import()
        self.assertEqual(bom.td_part_ids.mapped('name'), ['Боковина', 'Полиця'])
        side = bom.td_part_ids[0]
        self.assertEqual((side.length_mm, side.width_mm, side.qty, side.edge_long_sides), (720, 560, 2, 1))
        self.assertEqual(side.material_id, self.board_a)
