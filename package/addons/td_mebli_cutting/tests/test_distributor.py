from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.td_mebli_sale.tests.common import TdMebliSaleCommon


@tagged('post_install', '-at_install')
class TestCuttingAtDistributor(TdMebliSaleCommon):
    """A3 (F-28): the cutting at the distributor is a standard purchase of the cutting service; the expected return of
    the parts (purchase line date) plus the manufacturing lead time moves the forecast date, reason «cutting»."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.template_bom.produce_delay = 5
        cls.distributor = env['res.partner'].create({'name': 'Test board distributor'})
        cls.service = env['product.product'].create({
            'name': 'Board cutting', 'type': 'service', 'td_material_kind': 'cutting', 'purchase_ok': True,
            'seller_ids': [(0, 0, {'partner_id': cls.distributor.id, 'price': 1500.0, 'delay': 20})]})

    def _job(self, promised_in):
        order = self._make_order()
        start = fields.Date.context_today(order, order.date_order)
        order.commitment_date = fields.Datetime.to_datetime(start + timedelta(days=promised_in))
        order.action_confirm()
        action = order.mrp_production_ids.action_td_create_cutting_job()
        job = self.env['td.mebli.cutting.job'].browse(action['res_id'])
        return order, job

    def test_send_to_distributor_is_a_standard_purchase(self):
        order, job = self._job(40)
        job.action_send_distributor()
        self.assertEqual(job.state, 'sent')
        purchase = job.purchase_id
        self.assertEqual(purchase.partner_id, self.distributor, "the distributor comes from the vendor pricelist")
        self.assertEqual(purchase.state, 'purchase')
        self.assertEqual(purchase.order_line.product_id, self.service)
        self.assertTrue(purchase.message_ids.attachment_ids, "the cutting file goes with the purchase")
        expected = fields.Date.context_today(job, purchase.order_line.date_planned)
        self.assertEqual(job.return_date, expected, "the return date is read from the purchase line, not entered")
        self.assertEqual(job.distributor_id, self.distributor)

    def test_cutting_moves_the_forecast_date(self):
        order, job = self._job(10)
        before = order.td_forecast_date
        job.action_send_distributor()
        order.invalidate_recordset()
        ready = job.return_date + timedelta(days=5)
        self.assertGreaterEqual(ready, before)
        self.assertEqual(order.td_shop_date, ready)
        self.assertEqual(order.td_forecast_date, ready)
        self.assertGreater(order.td_delay_days, 0)
        self.assertEqual(order.td_delay_reason, 'cutting')
        self.assertIn(self.distributor.name, order.td_late_item)
        # the buyer changes the date in the purchase (the only place of input): the forecast follows
        job.purchase_id.order_line.date_planned = fields.Datetime.to_datetime(job.return_date + timedelta(days=3))
        order.invalidate_recordset()
        job.invalidate_recordset()
        self.assertEqual(order.td_forecast_date, ready + timedelta(days=3))
        # the parts are back (result received): the cutting no longer moves the date
        job.state = 'result'
        order.invalidate_recordset()
        job.invalidate_recordset()
        self.assertFalse(job.return_date)
        self.assertNotEqual(order.td_delay_reason, 'cutting')

    def test_no_cutting_service_is_explained(self):
        self.service.td_material_kind = False
        _order, job = self._job(40)
        with self.assertRaises(UserError):
            job.action_send_distributor()
