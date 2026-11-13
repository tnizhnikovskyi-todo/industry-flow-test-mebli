from odoo.tests import tagged

from .common import TdMebliSaleCommon


@tagged('post_install', '-at_install')
class TestContract(TdMebliSaleCommon):
    """A2: the printed contract of the order — two texts by the parameter, the payment schedule from the standard terms,
    the mark «template to be checked by a lawyer»."""

    def test_contract_two_modes_and_schedule(self):
        env = self.env
        term = env['account.payment.term'].create({'name': '50/40/10', 'line_ids': [
            (0, 0, {'value': 'percent', 'value_amount': 50.0, 'nb_days': 0, 'td_milestone': 'order'}),
            (0, 0, {'value': 'percent', 'value_amount': 40.0, 'nb_days': 14, 'td_milestone': 'install'}),
            (0, 0, {'value': 'percent', 'value_amount': 10.0, 'nb_days': 30, 'td_milestone': 'act'})]})
        order = self._make_order()
        order.payment_term_id = term
        rows = order._td_payment_schedule()
        self.assertEqual([row['milestone'] for row in rows], ['Prepayment', 'Before installation', 'After the act'])
        self.assertAlmostEqual(sum(row['amount'] for row in rows), order.amount_total)
        report = env['ir.actions.report']
        html, _kind = report._render_qweb_html('td_mebli_sale.report_contract', order.ids)
        self.assertIn(b'Contract Work Agreement', html)
        self.assertIn(b'chapter 61', html)
        self.assertIn(b'checked by a lawyer', html)
        self.assertIn(b'After the act', html)
        settings = env['res.config.settings'].create({'td_mebli_contract_mode': 'sale'})
        settings.execute()
        html, _kind = report._render_qweb_html('td_mebli_sale.report_contract', order.ids)
        self.assertIn(b'Sale Contract', html)
        self.assertIn(b'chapter 54', html)
