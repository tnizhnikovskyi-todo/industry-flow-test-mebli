from odoo.tests import TransactionCase, tagged

from odoo.addons.td_mebli_demo.scenario import run


@tagged('post_install', '-at_install')
class TestDashboardOnDemoData(TransactionCase):

    def test_figures_match_the_orders(self):
        result = run(self.env, 5)
        orders = result['order'] | result['dresser_order']
        dashboard = self.env['td.mebli.dashboard']
        cards = dashboard.get_data()['cards']
        revenue, margin = sum(orders.mapped('amount_untaxed')), sum(orders.mapped('margin'))
        self.assertGreater(revenue, 0)
        self.assertEqual(cards['revenue']['value'], dashboard._money(revenue))
        # the average margin is weighted (margin / revenue), the same as the totals of the margin report
        self.assertEqual(cards['margin']['value'], f"{dashboard._num(margin / revenue * 100)} %")
        self.assertIn(dashboard._money(margin), cards['margin']['lines'][0])
        self.assertEqual(cards['margin']['alert'], '')
        self.assertIn(str(len(orders)), cards['revenue']['lines'][0])
