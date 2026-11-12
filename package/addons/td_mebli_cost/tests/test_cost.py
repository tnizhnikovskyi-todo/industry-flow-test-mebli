from odoo.tests import tagged

from odoo.addons.td_mebli_sale.tests.common import TdMebliSaleCommon


@tagged('post_install', '-at_install')
class TestCost(TdMebliSaleCommon):

    def test_plan_and_actual(self):
        order = self._make_order()
        order.action_confirm()
        self.assertFalse(order.td_cost_has_fact)
        self.assertAlmostEqual(order.td_cost_plan, order.amount_untaxed - order.margin)
        production = order.mrp_production_ids
        production.workorder_ids.write({'duration': 60.0})
        production.workorder_ids.workcenter_id.write({'costs_hour': 300.0})
        production.qty_producing = 1
        for move in production.move_raw_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        production.with_context(skip_consumption=True).button_mark_done()
        order.invalidate_recordset()
        self.assertTrue(order.td_cost_has_fact)
        work = 300.0 * len(production.workorder_ids)
        self.assertAlmostEqual(order.td_cost_work, work)
        self.assertGreater(order.td_cost_material, 0)
        self.assertAlmostEqual(order.td_cost_fact, order.td_cost_material + work)
        self.assertAlmostEqual(order.td_margin_fact, order.amount_untaxed - order.td_cost_fact)
