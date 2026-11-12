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
