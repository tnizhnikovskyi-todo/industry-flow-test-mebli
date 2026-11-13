from odoo.exceptions import AccessError
from odoo.tests import tagged

from odoo.addons.td_mebli_sale.tests.common import TdMebliSaleCommon


@tagged('post_install', '-at_install')
class TestCost(TdMebliSaleCommon):

    def _finish(self, order, extra=0.0):
        production = order.mrp_production_ids
        production.workorder_ids.write({'duration': 60.0})
        production.workorder_ids.workcenter_id.write({'costs_hour': 300.0})
        production.qty_producing = 1
        for index, move in enumerate(production.move_raw_ids):
            move.quantity = move.product_uom_qty + (extra if index == 0 else 0.0)
            move.picked = True
        production.with_context(skip_consumption=True).button_mark_done()
        order.invalidate_recordset()
        return production

    def test_plan_and_actual(self):
        order = self._make_order()
        order.action_confirm()
        self.assertFalse(order.td_cost_has_fact)
        self.assertEqual(order.td_cost_status, "No actual yet")  # AC-114: unfinished manufacturing
        self.assertAlmostEqual(order.td_cost_plan, order.amount_untaxed - order.margin)
        production = self._finish(order)
        self.assertTrue(order.td_cost_has_fact)
        self.assertFalse(order.td_cost_status)
        work = 300.0 * len(production.workorder_ids)
        self.assertAlmostEqual(order.td_cost_work, work)
        self.assertGreater(order.td_cost_material, 0)
        self.assertAlmostEqual(order.td_cost_fact, order.td_cost_material + work)
        self.assertAlmostEqual(order.td_margin_fact, order.amount_untaxed - order.td_cost_fact)

    def test_ac_114_cutting_piecework_and_crew(self):
        env = self.env
        order = self._make_order()
        order.action_confirm()
        production = order.mrp_production_ids
        # the cutting at the distributor: a confirmed purchase of the service for the job of the order
        vendor = env['res.partner'].create({'name': 'Distributor'})
        cutting = env['product.product'].create({'name': 'Cutting service', 'type': 'service'})
        purchase = env['purchase.order'].create({'partner_id': vendor.id, 'order_line': [
            (0, 0, {'product_id': cutting.id, 'product_qty': 1.0, 'price_unit': 800.0, 'tax_ids': [(5, 0, 0)]})]})
        purchase.button_confirm()
        env['td.mebli.cutting.job'].create({'production_ids': [(6, 0, production.ids)], 'purchase_id': purchase.id})
        self._finish(order)
        # confirmed accruals: piecework of its work orders and the crew percent of its acts
        employee = env['hr.employee'].create({'name': 'Worker'})
        productive = env['mrp.workcenter.productivity.loss'].search([('loss_type', '=', 'productive')], limit=1)
        workorder = production.workorder_ids[:1]
        line = env['mrp.workcenter.productivity'].create({
            'workorder_id': workorder.id, 'workcenter_id': workorder.workcenter_id.id, 'loss_id': productive.id,
            'td_employee_id': employee.id, 'date_start': '2026-11-02 08:00:00', 'date_end': '2026-11-02 09:00:00'})
        piece = env['td.mebli.accrual'].create({'employee_id': employee.id, 'kind': 'piece', 'amount': 150.0})
        piece.sudo().productivity_id = line
        project = env['project.project'].create({'name': 'Installation'})
        task = env['project.task'].create({'name': 'Visit', 'project_id': project.id})
        task.sale_order_id = order
        act = env['td.mebli.install.act'].create({'task_id': task.id, 'kind': 'final', 'crew_pct': 0.0})
        crew = env['td.mebli.accrual'].create({'employee_id': employee.id, 'kind': 'crew', 'amount': 400.0})
        crew.sudo().act_id = act
        draft = env['td.mebli.accrual'].create({'employee_id': employee.id, 'kind': 'crew', 'amount': 9999.0})
        draft.sudo().act_id = act
        (piece | crew).action_td_confirm()
        order.invalidate_recordset()
        self.assertAlmostEqual(order.td_cost_cutting, 800.0)
        self.assertAlmostEqual(order.td_cost_piece, 150.0)
        self.assertAlmostEqual(order.td_cost_crew, 400.0)  # the draft accrual is not counted
        work = order.td_cost_work
        self.assertAlmostEqual(order.td_cost_fact, order.td_cost_material + work + 800.0 + 400.0)
        # parameter of the report: the piecework instead of the hours (no double count)
        order.company_id.td_cost_piecework = True
        order.invalidate_recordset()
        self.assertAlmostEqual(order.td_cost_fact, order.td_cost_material + 150.0 + 800.0 + 400.0)

    def test_ac_115_cost_only_for_the_finance(self):
        env = self.env
        order = self._make_order()
        order.action_confirm()
        salesman = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Seller', 'login': 'td_g3_cost_seller',
            'group_ids': [(6, 0, [env.ref('sales_team.group_sale_salesman_all_leads').id])]})
        with self.assertRaises(AccessError):
            order.with_user(salesman).read(['td_cost_fact'])
        with self.assertRaises(AccessError):
            order.with_user(salesman).read(['td_margin_fact'])
        menu = env.ref('td_mebli_cost.sale_order_td_cost_fact_menu')
        self.assertNotIn(menu.id, env['ir.ui.menu'].with_user(salesman)._visible_menu_ids())
        finance = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Finance', 'login': 'td_g3_cost_fin', 'group_ids': [(6, 0, [
                env.ref('sales_team.group_sale_salesman_all_leads').id, env.ref('td_mebli_base.group_finance').id])]})
        self.assertIn(menu.id, env['ir.ui.menu'].with_user(finance)._visible_menu_ids())
        order.with_user(finance).read(['td_cost_fact', 'td_margin_fact', 'td_cost_plan'])
        fields_info = order.with_user(salesman).fields_get(['td_cost_fact', 'td_cost_material'])
        self.assertFalse(fields_info)

    def test_ac_116_overconsumption_filter(self):
        normal = self._make_order()
        normal.action_confirm()
        self._finish(normal)
        over = self._make_order()
        over.action_confirm()
        self._finish(over, extra=2.0)
        self.assertTrue(over.td_overconsumption)
        self.assertFalse(normal.td_overconsumption)
        found = self.env['sale.order'].search([('td_overconsumption', '=', True)])
        self.assertIn(over, found)
        self.assertNotIn(normal, found)
        search = self.env.ref('td_mebli_cost.sale_order_td_cost_fact_search').arch
        self.assertIn('name="td_overconsumption" string="Overconsumption"', search)
