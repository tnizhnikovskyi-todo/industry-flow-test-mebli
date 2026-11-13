from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPriceHistory(TransactionCase):

    def test_price_above_the_average_of_earlier_purchases(self):
        env = self.env
        vendor = env['res.partner'].create({'name': 'Vendor'})
        product = env['product.product'].create({'name': 'Hinge', 'type': 'consu'})
        now = fields.Datetime.now()

        def buy(price, days_ago, qty=10):
            order = env['purchase.order'].create({'partner_id': vendor.id, 'date_order': now - timedelta(days=days_ago),
                                                  'order_line': [(0, 0, {'product_id': product.id, 'product_qty': qty,
                                                                         'price_unit': price})]})
            order.button_confirm()
            order.date_order = now - timedelta(days=days_ago)
            return order.order_line

        buy(40.0, 60)
        buy(44.0, 30)
        line = buy(50.0, 1)
        line.invalidate_recordset()
        line._compute_td_history_price()
        self.assertAlmostEqual(line.td_history_price, 42.0)
        self.assertTrue(line.td_over_history)
        self.assertAlmostEqual(line.td_overpay, 80.0)
        old = buy(30.0, 400)
        old._compute_td_history_price()
        self.assertFalse(old.td_over_history)  # no history in 180 days before it

    def test_ac_085_threshold_from_the_company(self):
        """VP-11: the threshold «price above history» is the parameter of the company (td_mebli_base), not a constant."""
        env = self.env
        vendor = env['res.partner'].create({'name': 'Vendor'})
        product = env['product.product'].create({'name': 'Handle', 'type': 'consu'})
        now = fields.Datetime.now()

        def buy(price, days_ago):
            order = env['purchase.order'].create({'partner_id': vendor.id, 'date_order': now - timedelta(days=days_ago),
                                                  'order_line': [(0, 0, {'product_id': product.id, 'product_qty': 10,
                                                                         'price_unit': price})]})
            order.button_confirm()
            order.date_order = now - timedelta(days=days_ago)
            return order.order_line

        buy(100.0, 30)
        line = buy(108.0, 1)  # +8 %
        env.company.td_price_threshold_pct = 5.0
        line._compute_td_history_price()
        self.assertTrue(line.td_over_history)
        env.company.td_price_threshold_pct = 10.0
        line._compute_td_history_price()
        self.assertFalse(line.td_over_history)

    def test_ac_086_no_history_no_mark_and_a_hint(self):
        env = self.env
        vendor = env['res.partner'].create({'name': 'Vendor'})
        product = env['product.product'].create({'name': 'New hinge', 'type': 'consu'})
        order = env['purchase.order'].create({'partner_id': vendor.id, 'order_line': [
            (0, 0, {'product_id': product.id, 'product_qty': 5, 'price_unit': 70.0})]})
        line = order.order_line
        self.assertFalse(line.td_over_history)
        self.assertFalse(line.td_history_price)  # the column of the history is empty
        self.assertEqual(line.td_history_note, 'no history')
        self.assertFalse(line.td_overpay)
        order.button_confirm()  # no error

    def test_ac_085_mark_above_history_with_the_percent(self):
        env = self.env
        env.company.td_price_threshold_pct = 5.0
        vendor = env['res.partner'].create({'name': 'Vendor'})
        product = env['product.product'].create({'name': 'Drawer runner', 'type': 'consu'})
        now = fields.Datetime.now()
        old = env['purchase.order'].create({'partner_id': vendor.id, 'date_order': now - timedelta(days=20),
                                            'order_line': [(0, 0, {'product_id': product.id, 'product_qty': 10,
                                                                   'price_unit': 100.0})]})
        old.button_confirm()
        old.date_order = now - timedelta(days=20)
        line = env['purchase.order'].create({'partner_id': vendor.id, 'order_line': [
            (0, 0, {'product_id': product.id, 'product_qty': 10, 'price_unit': 108.0})]}).order_line
        line._compute_td_history_price()
        self.assertTrue(line.td_over_history)
        self.assertEqual(line.td_history_note, 'Above history +8 %')
        self.assertAlmostEqual(line.td_overpay, 80.0)
        over = env['purchase.order.line'].search([('td_over_history', '=', True), ('id', '=', line.id)])
        self.assertEqual(over, line)  # the filter «Above history»
