from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TdMebliCommon


@tagged('post_install', '-at_install')
class TestOrderBom(TdMebliCommon):

    def _generate(self, dims=None, selections=None):
        return self.env['mrp.bom']._td_generate_order_bom(
            self.cabinet, dims or self.dims, selections or self.selections)

    def test_generate(self):
        bom = self._generate()
        self.assertTrue(bom.td_order_bom)
        self.assertEqual(bom.td_template_bom_id, self.template_bom)
        self.assertEqual(bom.td_part_count, 6)
        lines = {line.product_id: line.product_qty for line in bom.bom_line_ids}
        # body: 2 sides 0.7x0.5 + top 0.768x0.5 = 0.7+0.384 = 1.084 m2, +10 % waste
        self.assertAlmostEqual(lines[self.board_a], 1.084 * 1.1, places=2)
        # facade: 2 doors 0.696x0.396 = 0.551232 m2, +10 %
        self.assertAlmostEqual(lines[self.facade], 0.551232 * 1.1, places=2)
        self.assertAlmostEqual(lines[self.back], 0.79 * 0.69, places=2)
        # edge A: sides 2x0.7 + top 2x0.768, plus 3 edged sides... allowance 30 mm for every edged side
        edge_a = 2 * (0.7 + 0.03) + 2 * (0.768 + 0.03)
        self.assertAlmostEqual(lines[self.edge_a], edge_a, places=2)
        # edge on facade is 2 mm and exists only for the facade board
        edge_f = 2 * (2 * 0.696 + 2 * 0.396 + 4 * 0.03)
        self.assertAlmostEqual(lines[self.edge_f], edge_f, places=2)
        self.assertEqual(lines[self.fitting], 1.0)
        self.assertEqual(self.env.ref('uom.product_uom_square_meter'),
                         bom.bom_line_ids.filtered(lambda line: line.product_id == self.board_a).product_uom_id)
        operations = {op.name: op.time_cycle_manual for op in bom.operation_ids}
        self.assertEqual(operations, {'Cutting': 12.0, 'Assembly': 60.0})
        self.assertEqual(bom.td_width, 800)

    def test_generate_other_dims_changes_quantities(self):
        small = self._generate({'width': 400, 'height': 500, 'depth': 300})
        big = self._generate()
        qty = lambda bom: sum(bom.bom_line_ids.filtered(lambda l: l.product_id == self.board_a).mapped('product_qty'))
        self.assertLess(qty(small), qty(big))

    def test_out_of_range(self):
        with self.assertRaises(UserError):
            self._generate({'width': 3000, 'height': 700, 'depth': 500})

    def test_missing_edge(self):
        # board B has only 0.4 mm edge
        with self.assertRaises(UserError):
            self._generate(selections=self.val_b | self.val_f | self.val_e2)

    def test_bom_find_excludes_order_bom(self):
        bom = self._generate()
        found = self.env['mrp.bom']._bom_find(self.cabinet)[self.cabinet]
        self.assertEqual(found, self.template_bom)
        self.assertNotEqual(found, bom)

    def test_bom_cost(self):
        bom = self._generate()
        cost = self.cabinet._compute_bom_price(bom)
        materials = sum(
            line.product_id.standard_price * line.product_qty for line in bom.bom_line_ids)
        operations = 12.0 / 60 * 600.0 + 60.0 / 60 * 300.0
        self.assertAlmostEqual(cost, materials + operations, places=2)
