from odoo.tests import tagged

from .common import TdMebliSaleCommon


@tagged('post_install', '-at_install')
class TestSaleFlow(TdMebliSaleCommon):

    def test_confirm_creates_mo(self):
        order = self._make_order()
        order.action_confirm()
        line = order.order_line
        self.assertTrue(line.td_bom_id.td_order_bom)
        self.assertEqual(line.td_bom_id.td_sale_line_id, line)
        mo = order.mrp_production_ids
        self.assertEqual(len(mo), 1)
        self.assertEqual(mo.bom_id, line.td_bom_id)
        self.assertEqual(mo.sale_line_id, line)
        self.assertEqual(len(mo.workorder_ids), 2)
        self.assertEqual(order.mrp_production_count, 1)

    def test_two_orders_two_boms(self):
        order1 = self._make_order(width=800)
        order2 = self._make_order(width=1200)
        (order1 | order2).action_confirm()
        bom1, bom2 = order1.order_line.td_bom_id, order2.order_line.td_bom_id
        self.assertNotEqual(bom1, bom2)
        self.assertEqual(order1.mrp_production_ids.bom_id, bom1)
        self.assertEqual(order2.mrp_production_ids.bom_id, bom2)
        self.assertEqual((bom1.td_width, bom2.td_width), (800, 1200))

    def test_generate_in_draft_and_rebuild(self):
        order = self._make_order()
        line = order.order_line
        line.action_td_generate_bom()
        first = line.td_bom_id
        self.assertTrue(first)
        line.td_width = 1100
        line.action_td_generate_bom()
        self.assertNotEqual(line.td_bom_id, first)
        self.assertFalse(first.exists())
        self.assertEqual(line.td_bom_id.td_width, 1100)

    def test_margin(self):
        order = self._make_order()
        line = order.order_line
        line.action_td_generate_bom()
        expected = line.product_id._compute_bom_price(line.td_bom_id)
        self.assertGreater(expected, 0)
        self.assertAlmostEqual(line.purchase_price, expected, places=2)
        self.assertAlmostEqual(line.margin, line.price_subtotal - expected, places=2)
        self.assertAlmostEqual(
            line.td_planned_material_cost + line.td_planned_operation_cost, expected, places=2)
