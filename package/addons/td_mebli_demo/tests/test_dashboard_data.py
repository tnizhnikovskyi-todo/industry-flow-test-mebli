from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged

from odoo.addons.td_mebli_demo.scenario import run


@tagged('post_install', '-at_install')
class TestDashboardOnDemoData(TransactionCase):
    """Works on a clean test database and on a show database with the seeded order book: the card is compared with the
    orders it says it counts, not with fixed numbers."""

    def test_figures_match_the_orders(self):
        run(self.env, 5)
        dashboard = self.env['td.mebli.dashboard']
        data = dashboard.get_data()
        card = data['by_key']['margin']
        since = fields.Datetime.to_datetime(fields.Date.context_today(dashboard) - timedelta(days=30))
        orders = self.env['sale.order'].search([('state', '=', 'sale'), ('company_id', '=', self.env.company.id),
                                                ('date_order', '>=', since)])
        revenue, margin = sum(orders.mapped('amount_untaxed')), sum(orders.mapped('margin'))
        self.assertGreater(revenue, 0)
        # one weighted margin (margin ÷ revenue): the card, its drill-down and the reports
        self.assertEqual(card['value'], dashboard._pct(margin / revenue * 100))
        self.assertEqual(set(card['drill']['ids']), set(orders.ids))
        self.assertIn(dashboard._money(margin), card['lines'][0])
        # every card opens exactly the records it counted
        for item in data['cards']:
            records = self.env[item['drill']['res_model']].browse(item['drill']['ids'])
            self.assertEqual(len(records.exists()), len(item['drill']['ids']))
