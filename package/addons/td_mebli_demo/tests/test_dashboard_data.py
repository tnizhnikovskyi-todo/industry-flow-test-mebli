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

    def test_finance_role_opens_every_card(self):
        """The finance role of the demo (no manufacturing, purchase or project group) opens the drill-down of all the
        cards (11; 12 with the quality feature of box B): the list views load and read the records the card counted."""
        from lxml import etree

        from odoo.addons.td_mebli_demo.showcase import USERS
        run(self.env, 5)
        # the load card counts the open work of the next 7 days: plan the open work orders for today
        open_wo = self.env['mrp.workorder'].search([('state', 'not in', ('done', 'cancel'))])
        open_wo.with_context(bypass_duration_calculation=True).write({'date_start': fields.Datetime.now()})
        self.assertTrue(open_wo)
        groups = next(row[4] for row in USERS if row[0] == 'fin')
        fin = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Finance', 'login': 'td_fin_test', 'group_ids': [(6, 0, [self.env.ref(g).id for g in groups])]})
        data = self.env['td.mebli.dashboard'].with_user(fin).get_data()
        # box B of the demo (settings_data.xml): the quality feature adds the 12th card (AC-121)
        quality = fin.has_group('td_mebli_base.group_feature_quality')
        self.assertEqual(len(data['cards']), 12 if quality else 11)
        self.assertTrue(data['by_key']['load']['drill']['ids'])
        for card in data['cards']:
            drill = card['drill']
            Model = self.env[drill['res_model']].with_user(fin)
            Model.check_access('read')  # also for an empty drill-down (the search of no ids does not check the access)
            Model.browse(drill['ids']).check_access('read')
            views = Model.get_views([tuple(view) for view in drill['views']])
            for kind, view in views['views'].items():
                if kind not in ('list', 'pivot'):
                    continue
                names = {node.get('name') for node in etree.fromstring(view['arch']).iter('field')}
                spec = {name: {'fields': {'display_name': {}}} if Model._fields[name].type == 'many2one' else {}
                        for name in names if name in Model._fields}
                with self.subTest(card=card['key'], view=kind):
                    result = Model.web_search_read([('id', 'in', drill['ids'])], spec)
                    self.assertEqual(result['length'], len(drill['ids']))

    def test_finance_role_accrues(self):
        from odoo.addons.td_mebli_demo.showcase import USERS
        run(self.env, 5)
        groups = next(row[4] for row in USERS if row[0] == 'fin')
        fin = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Finance', 'login': 'td_fin_test2', 'group_ids': [(6, 0, [self.env.ref(g).id for g in groups])]})
        self.env['td.mebli.accrual'].with_user(fin).action_td_accrue()
        self.env['td.mebli.accrual'].with_user(fin).web_search_read([], {'workcenter_id': {'fields': {'display_name': {}}},
                                                                         'order_ref': {}, 'amount': {}})
