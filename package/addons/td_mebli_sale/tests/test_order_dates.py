from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import TdMebliSaleCommon


@tagged('post_install', '-at_install')
class TestOrderDates(TdMebliSaleCommon):
    """S-02: promised and forecast date, the shift and its reason (F-23, F-31, NG-01).

    The made-to-order item is bought by the standard: a component with the routes MTO + Buy and a vendor pricelist line;
    the confirmation of the sales order creates the purchase order, the supplier date is the purchase line date_planned."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.supplier = env['res.partner'].create({'name': 'Test paint shop'})
        cls.fronts = env['product.product'].create({
            'name': 'Painted fronts', 'type': 'consu', 'is_storable': True, 'standard_price': 900.0,
            'route_ids': [(6, 0, [env.ref('stock.route_warehouse0_mto').id, env.ref('purchase_stock.route_warehouse0_buy').id])],
            'seller_ids': [(0, 0, {'partner_id': cls.supplier.id, 'price': 900.0, 'delay': 10})],
        })
        cls.template_bom.write({
            'produce_delay': 5,
            'bom_line_ids': [(0, 0, {'product_id': cls.fronts.id, 'product_qty': 2.0})],
        })

    def _order(self, promised_in):
        order = self._make_order()
        start = fields.Date.context_today(order, order.date_order)
        order.commitment_date = fields.Datetime.to_datetime(start + timedelta(days=promised_in))
        return order, start

    def _confirmed(self, promised_in):
        order, start = self._order(promised_in)
        order.action_confirm()
        return order, start

    def _reread(self, order):
        order.invalidate_recordset()
        order._get_purchase_orders().order_line.invalidate_recordset()
        # the forecast is stored (AC-066): the receipts and the history of the supplier are not stored dependencies,
        # the write hooks and the daily scheduled action recompute it
        order._td_recompute_forecast()
        return order

    def test_quotation_the_workshop_decides(self):
        order, start = self._order(20)
        # a quotation has no manufacturing order: the lead time of the order BoM (copied from the template BoM)
        self.assertEqual(order.td_shop_date, start + timedelta(days=5))
        self.assertEqual(order.td_forecast_date, start + timedelta(days=5))
        self.assertEqual(order.td_delay_days, 0)
        self.assertFalse(order.td_delay_reason)
        self.assertFalse(order.td_purchase_line_ids)

    def test_confirmation_creates_the_purchase_by_the_standard(self):
        order, _start = self._confirmed(30)
        purchases = order._get_purchase_orders()
        self.assertEqual(len(purchases), 1, "MTO + Buy: the confirmation creates one request for quotation")
        self.assertEqual(purchases.partner_id, self.supplier, "the supplier comes from the vendor pricelist")
        self.assertEqual(order.purchase_order_count, 1, "the smart button of sale_purchase counts it")
        line = purchases.order_line
        self.assertEqual(line.product_id, self.fronts)
        self.assertEqual(line._td_production(), order.mrp_production_ids, "the purchase feeds the manufacturing order")
        self.assertEqual(order.td_purchase_line_ids, line)

    def test_late_supplier_date_moves_the_forecast(self):
        order, start = self._confirmed(20)
        line = order._get_purchase_orders().order_line
        # the buyer enters the date of the supplier in the purchase order (the only place of input)
        line.date_planned = fields.Datetime.to_datetime(start + timedelta(days=25)) + timedelta(hours=10)
        self._reread(order)
        self.assertEqual(line.td_date_ready, start + timedelta(days=30), "arrival + manufacturing lead time of the BoM")
        self.assertEqual(order.td_forecast_date, start + timedelta(days=30))
        self.assertEqual(order.td_delay_days, 10)
        self.assertEqual(order.td_delay_reason, 'supplier')
        self.assertEqual(order.td_late_line_id, line)
        self.assertIn(self.supplier.name, order.td_late_item)

    def test_received_item_no_longer_moves_the_date(self):
        order, start = self._confirmed(20)
        purchase = order._get_purchase_orders()
        purchase.order_line.date_planned = fields.Datetime.to_datetime(start + timedelta(days=25))
        purchase.button_confirm()
        receipt = purchase.picking_ids
        receipt.move_ids.quantity = 2.0
        receipt.move_ids.picked = True
        receipt.button_validate()
        self._reread(order)
        self.assertFalse(purchase.order_line.td_date_ready)
        self.assertEqual(order.td_delay_days, 0)
        self.assertFalse(order.td_late_line_id)

    def test_workshop_shift_is_the_company_reason(self):
        order, start = self._confirmed(20)
        line = order._get_purchase_orders().order_line
        line.date_planned = fields.Datetime.to_datetime(start - timedelta(days=10))  # the item comes in time
        self._reread(order)
        shop = order.td_shop_date
        order.commitment_date = fields.Datetime.to_datetime(shop - timedelta(days=3))  # promised before the workshop end
        self._reread(order)
        self.assertEqual(order.td_forecast_date, shop)
        self.assertEqual(order.td_delay_days, 3)
        self.assertEqual(order.td_delay_reason, 'company')
        self.assertFalse(order.td_late_line_id)
        self.assertFalse(order.td_late_item)

    def test_salesperson_without_purchase_rights_gets_the_forecast(self):
        order, start = self._confirmed(20)
        order._get_purchase_orders().order_line.date_planned = fields.Datetime.to_datetime(start + timedelta(days=25))
        salesman = self.env['res.users'].create({
            'name': 'Salesman', 'login': 'td_salesman_dates',
            'group_ids': [(6, 0, [self.env.ref('sales_team.group_sale_salesman_all_leads').id])]})
        as_salesman = order.with_user(salesman)
        self.assertEqual(as_salesman.td_delay_days, 10)
        self.assertEqual(as_salesman.td_delay_reason, 'supplier')
        self.assertIn(self.supplier.name, as_salesman.td_late_item)

    def _salesman(self, login, group='sales_team.group_sale_salesman'):
        return self.env['res.users'].create({
            'name': login, 'login': login,
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id, self.env.ref(group).id])]})

    def test_salesperson_reads_the_purchases_of_his_orders_only(self):
        """Read-only access to purchase.order(.line) for a salesperson, limited by the rule «purchases of my orders»."""
        mine, start = self._confirmed(20)
        other, _start = self._confirmed(20)
        salesman = self._salesman('td_salesman_own')
        mine.user_id = salesman
        mine._get_purchase_orders().order_line.date_planned = fields.Datetime.to_datetime(start + timedelta(days=25))
        as_salesman = self._reread(mine).with_user(salesman)
        self.assertFalse(salesman.has_group('purchase.group_purchase_user'))
        lines = as_salesman.td_purchase_line_ids
        self.assertEqual(len(lines), 1)
        # the fields of the tab are read with his own rights (no sudo)
        values = lines.read(['product_id', 'partner_id', 'order_id', 'date_planned', 'qty_received', 'td_date_ready'])
        self.assertEqual(values[0]['td_date_ready'], start + timedelta(days=30))
        self.assertEqual(as_salesman.td_late_line_id, lines)
        with self.assertRaises(AccessError):
            lines.with_user(salesman).write({'date_planned': fields.Datetime.now()})
        with self.assertRaises(AccessError):
            lines.order_id.with_user(salesman).button_confirm()
        theirs = other._get_purchase_orders()
        if theirs != mine._get_purchase_orders():  # a merged request for quotation is read by both salespersons
            with self.assertRaises(AccessError):
                theirs.with_user(salesman).read(['name'])
        self.assertEqual(self.env['sale.order']._fields['purchase_order_count'].groups, 'purchase.group_purchase_user',
                         "the smart button stays with Purchase (standard group)")

    def test_merged_request_shows_only_the_lines_of_the_order(self):
        """Two orders, the same supplier: the buyer merges the requests for quotation (standard action_merge, the merged
        request keeps the references of both, purchase_stock _merge_po_post_process); each order sees only its line."""
        first, start = self._confirmed(20)
        second, _start = self._confirmed(20)
        own, other = first._get_purchase_orders(), second._get_purchase_orders()
        other.order_line.date_planned = fields.Datetime.to_datetime(start + timedelta(days=40))  # not merged into one line
        (own | other).action_merge()
        merged = first._get_purchase_orders().filtered(lambda po: po.state != 'cancel')
        self.assertEqual(merged, second._get_purchase_orders().filtered(lambda po: po.state != 'cancel'))
        self.assertEqual(len(merged.order_line), 2)
        self._reread(first)
        self._reread(second)
        self.assertEqual(len(first.td_purchase_line_ids), 1)
        self.assertEqual(len(second.td_purchase_line_ids), 1)
        self.assertEqual(first.td_purchase_line_ids._td_production(), first.mrp_production_ids)
        self.assertEqual(second.td_purchase_line_ids._td_production(), second.mrp_production_ids)

    def test_two_step_receipt_follows_the_chain(self):
        """Receipt in 2 steps: the purchase line feeds the input move; the chain of destination moves reaches the MO."""
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
        warehouse.reception_steps = 'two_steps'
        order, start = self._confirmed(20)
        line = order._get_purchase_orders().order_line
        self.assertEqual(line._td_production(), order.mrp_production_ids)
        self.assertEqual(order.td_purchase_line_ids, line)
        line.date_planned = fields.Datetime.to_datetime(start + timedelta(days=25)) + timedelta(hours=10)
        self._reread(order)
        self.assertEqual(line.td_date_ready, start + timedelta(days=30))

    def test_stage_drag_needs_manufacturing_rights(self):
        """The board: a salesperson cannot start the production by moving the card (no sudo); a manufacturing user can."""
        order, _start = self._confirmed(20)
        salesman = self._salesman('td_salesman_stage')
        order.user_id = salesman
        with self.assertRaises(UserError):
            order.with_user(salesman).td_stage = 'progress'
        worker = self.env['res.users'].create({
            'name': 'Worker', 'login': 'td_mrp_stage', 'group_ids': [(6, 0, [
                self.env.ref('mrp.group_mrp_user').id, self.env.ref('sales_team.group_sale_salesman_all_leads').id])]})
        order.with_user(worker).td_stage = 'progress'
        self.assertTrue(order.mrp_production_ids.workorder_ids.filtered(lambda w: w.state == 'progress'))

    def test_no_parallel_accounting(self):
        """§23: the date fields of the order are computed and read only, no supplier or date is entered in the order."""
        names = ['td_purchase_line_ids', 'td_shop_date', 'td_forecast_date', 'td_delay_days', 'td_late_line_id',
                 'td_late_item', 'td_delay_reason']
        for name in names:
            field = self.env['sale.order']._fields[name]
            # stored since A-11 (the board groups by the reason, AC-066) — still computed, never entered
            self.assertTrue(field.compute and field.readonly, name)
        self.assertNotIn('td.mebli.order.item', self.env)

    def test_cron_recomputes_only_open_orders_in_batches(self):
        """Review A-11: the daily cron takes the confirmed orders that are not delivered in full, in batches."""
        open_order, _start = self._confirmed(20)
        quotation, _start = self._order(20)
        domain = self.env['sale.order']._td_forecast_open_domain()
        found = self.env['sale.order'].search(domain)
        self.assertIn(open_order, found)
        self.assertNotIn(quotation, found)
        full = self.env['sale.order'].search(domain + [('delivery_status', '=', 'full')])
        self.assertFalse(full, "a delivered order is finished: its forecast is not recomputed")
        seen = []
        original = type(self.env['sale.order'])._td_recompute_forecast

        def spy(records):
            seen.append(records.ids)
            return original(records)
        self.env['ir.config_parameter'].sudo().set_param('td_mebli_sale.forecast_cursor', '0')
        with patch.object(type(self.env['sale.order']), '_td_recompute_forecast', spy):
            self.env['sale.order']._cron_td_recompute_forecast(batch_size=1)
        self.assertTrue(all(len(ids) == 1 for ids in seen))
        self.assertIn([open_order.id], seen)
        self.assertNotIn([quotation.id], seen)

    def test_delay_days_in_the_time_zone_of_the_company(self):
        """Review A-11: the promised day is the day in the time zone of the company, not of the computing user (the
        cron has none): 22:30 UTC is already the next day in Kyiv."""
        self.env.company.resource_calendar_id.tz = 'Europe/Kyiv'
        order, start = self._order(5)
        order.commitment_date = fields.Datetime.to_datetime(start + timedelta(days=4)) + timedelta(hours=22, minutes=30)
        self.assertEqual(order._td_company_date(order.commitment_date), start + timedelta(days=5))
        # the workshop needs 5 days: in Kyiv the promise is day 5 — no delay (UTC would say day 4, one day late)
        order.with_context(tz='UTC')._td_recompute_forecast()
        self.assertEqual(order.td_forecast_date, start + timedelta(days=5))
        self.assertEqual(order.td_delay_days, 0)

    def test_cron_continues_after_the_cursor(self):
        """Review A-11 (round 2): a run of the cron stopped after the first batch (time over) keeps the cursor; the
        next run recomputes the rest only; after the full pass the cursor is 0 again."""
        first, _start = self._confirmed(20)
        second, _start = self._confirmed(20)
        Param = self.env['ir.config_parameter'].sudo()
        Param.set_param('td_mebli_sale.forecast_cursor', '0')
        SaleOrder = type(self.env['sale.order'])
        IrCron = type(self.env['ir.cron'])
        seen = []
        original = SaleOrder._td_recompute_forecast

        def spy(records):
            seen.append(records.ids)
            return original(records)
        cron = self.env['sale.order'].with_context(ir_cron_progress_id=1)
        # the first call announces «remaining», the second (after the first batch) says the time is over
        with patch.object(SaleOrder, '_td_recompute_forecast', spy), \
                patch.object(IrCron, '_commit_progress', side_effect=[100.0, 0.0]) as progress:
            cron._cron_td_recompute_forecast(batch_size=1)
        open_ids = self.env['sale.order'].search(self.env['sale.order']._td_forecast_open_domain(), order='id').ids
        self.assertEqual(seen, [open_ids[:1]], "one batch, then the run stops")
        self.assertEqual(Param.get_param('td_mebli_sale.forecast_cursor'), str(open_ids[0]))
        self.assertEqual(progress.call_args_list[0].kwargs, {'remaining': len(open_ids)})
        seen.clear()
        with patch.object(SaleOrder, '_td_recompute_forecast', spy), \
                patch.object(IrCron, '_commit_progress', return_value=100.0):
            cron._cron_td_recompute_forecast(batch_size=1)
        self.assertEqual([ids[0] for ids in seen], open_ids[1:], "the second run goes on after the cursor")
        self.assertIn(second.id, open_ids)
        self.assertIn(first.id, open_ids)
        self.assertEqual(Param.get_param('td_mebli_sale.forecast_cursor'), '0', "full pass: the cursor is reset")
