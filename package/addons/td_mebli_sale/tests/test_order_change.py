from datetime import timedelta

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TdMebliSaleCommon


@tagged('post_install', '-at_install')
class TestOrderChange(TdMebliSaleCommon):

    def test_change_keeps_before_and_after(self):
        order = self._make_order()
        order.action_confirm()
        promised = order.date_order + timedelta(days=30)
        order.commitment_date = promised
        before = order.amount_untaxed
        self.env['td.mebli.order.change.wizard'].create(
            {'order_id': order.id, 'reason': 'customer', 'note': 'Other fronts'}).action_create()
        self.assertTrue(order.td_change_open)
        with self.assertRaises(UserError):
            self.env['td.mebli.order.change.wizard'].create(
                {'order_id': order.id, 'reason': 'customer', 'note': 'Again'}).action_create()
        order.order_line.price_unit += 1000.0
        order.commitment_date = promised + timedelta(days=7)
        order.action_td_fix_change()
        change = order.td_change_ids
        self.assertEqual((change.version, change.state, change.shift_days), (2, 'done', 7))
        self.assertAlmostEqual(change.amount_before, before)
        self.assertAlmostEqual(change.amount_delta, 1000.0)
