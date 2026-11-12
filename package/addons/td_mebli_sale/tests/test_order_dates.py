from datetime import timedelta

from odoo import fields
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

    def test_no_parallel_accounting(self):
        """§23: the date fields of the order are computed and read only, no supplier or date is entered in the order."""
        names = ['td_purchase_line_ids', 'td_shop_date', 'td_forecast_date', 'td_delay_days', 'td_late_line_id',
                 'td_late_item', 'td_delay_reason']
        for name in names:
            field = self.env['sale.order']._fields[name]
            self.assertTrue(field.compute and not field.store and field.readonly, name)
        self.assertNotIn('td.mebli.order.item', self.env)
