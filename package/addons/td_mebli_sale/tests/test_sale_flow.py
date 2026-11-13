from odoo import fields
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

    def test_hours_to_launch(self):
        order = self._make_order()
        order.action_confirm()
        self.assertFalse(order.td_launch_date)
        self.assertLess(order.td_hours_to_launch, 1.0)  # waiting for launch: counted from the order date so far
        workorder = order.mrp_production_ids.workorder_ids[:1]
        workorder.button_start()
        started = fields.Datetime.add(order.date_order, hours=30)
        workorder.time_ids.write({'date_start': started})
        order.invalidate_recordset(['td_launch_date', 'td_hours_to_launch'])
        self.assertEqual(order.td_launch_date, started)
        self.assertAlmostEqual(order.td_hours_to_launch, 30.0, places=1)

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

    def test_salesperson_builds_and_confirms(self):
        """A salesperson without manufacturing rights builds the specification and confirms the order."""
        user = self.env['res.users'].create({
            'name': 'Salesperson', 'login': 'td_mebli_salesperson',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id, self.env.ref('sales_team.group_sale_salesman').id])]})
        order = self._make_order()
        order.user_id = user
        order = order.with_user(user)
        order.order_line.action_td_generate_bom()
        self.assertTrue(order.order_line.td_bom_id)
        self.assertTrue(order.order_line.td_bom_id.td_part_ids)
        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        self.assertGreaterEqual(order.td_hours_to_launch, 0.0)  # readable without rights on work orders
        # the salesperson sees the manufacturing order: a button on the order and a line in the chatter
        self.assertEqual(order.td_production_count, 1)
        production = order.sudo().mrp_production_ids
        self.assertTrue(any(production.name in (message.body or '') for message in order.message_ids))
        action = order.action_td_view_production()
        self.assertEqual(action['res_model'], 'mrp.production')
        self.assertEqual(production.td_partner_id, order.partner_id)
