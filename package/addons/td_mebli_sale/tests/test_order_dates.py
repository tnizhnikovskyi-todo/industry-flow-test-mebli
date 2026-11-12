from datetime import timedelta

from psycopg2 import IntegrityError

from odoo import fields
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import TdMebliSaleCommon


@tagged('post_install', '-at_install')
class TestOrderDates(TdMebliSaleCommon):
    """S-02: promised and forecast date, the shift and its reason, made-to-order items (F-23, F-31, NG-01)."""

    def _order(self, promised_in):
        order = self._make_order()
        start = fields.Date.context_today(order, order.date_order)
        order.commitment_date = fields.Datetime.to_datetime(start + timedelta(days=promised_in))
        return order, start

    def _item(self, order, date_supplier, lead_days=3, state='confirmed'):
        return self.env['td.mebli.order.item'].create({
            'order_id': order.id, 'name': 'Painted fronts', 'date_supplier': date_supplier,
            'lead_days': lead_days, 'state': state})

    def test_without_items_the_workshop_decides(self):
        order, start = self._order(20)
        # a quotation has no manufacturing order: the default workshop time of a BoM without a lead time
        self.assertEqual(order.td_shop_date, start + timedelta(days=14))
        self.assertEqual(order.td_forecast_date, start + timedelta(days=14))
        self.assertEqual(order.td_delay_days, 0)
        self.assertFalse(order.td_delay_reason)

    def test_late_supplier_item_moves_the_date(self):
        order, start = self._order(20)
        item = self._item(order, start + timedelta(days=25))
        self.assertEqual(item.date_ready, start + timedelta(days=28))
        self.assertTrue(item.is_late)
        self.assertEqual(order.td_forecast_date, start + timedelta(days=28))
        self.assertEqual(order.td_delay_days, 8)
        self.assertEqual(order.td_delay_reason, 'supplier')
        self.assertEqual(order.td_late_item_id, item)

    def test_received_item_no_longer_moves_the_date(self):
        order, start = self._order(20)
        item = self._item(order, start + timedelta(days=25))
        item.state = 'received'
        self.assertFalse(item.date_ready)
        self.assertEqual(order.td_delay_days, 0)
        self.assertFalse(order.td_late_item_id)

    def test_workshop_shift_is_the_company_reason(self):
        order, start = self._order(10)
        self._item(order, start + timedelta(days=5))  # the item comes in time, the workshop does not
        self.assertEqual(order.td_delay_days, 4)
        self.assertEqual(order.td_delay_reason, 'company')
        self.assertFalse(order.td_late_item_id)

    def test_customer_reason_is_kept(self):
        order, start = self._order(20)
        item = self._item(order, start + timedelta(days=25))
        order.td_delay_reason = 'customer'
        item.date_supplier = start + timedelta(days=26)
        self.assertEqual(order.td_delay_reason, 'customer')
        self.assertEqual(order.td_delay_days, 9)

    def test_negative_days_to_fit_refused(self):
        order, start = self._order(20)
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError), self.cr.savepoint():
            self._item(order, start, lead_days=-1)
