from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged

KEYS = {'shift', 'on_time', 'stuck', 'margin', 'claims', 'payments', 'prices', 'load', 'ready', 'conversion', 'waste'}


@tagged('post_install', '-at_install')
class TestDashboard(TransactionCase):

    def _user(self, login, groups):
        return self.env['res.users'].with_context(no_reset_password=True).create({
            'name': login, 'login': login,
            'group_ids': [(6, 0, [self.env.ref(g).id for g in groups])]})

    def test_cards_of_the_a_box(self):
        data = self.env['td.mebli.dashboard'].get_data()
        self.assertEqual({card['key'] for card in data['cards']}, KEYS)  # BOX §11.1: KPI 1-10 + prices (quality: B)
        for card in data['cards']:
            drill = card['drill']
            self.assertIsInstance(drill['ids'], list)
            self.assertTrue(all(isinstance(view_id, int) for view_id, kind in drill['views'] if kind != 'form'))
        self.assertTrue(data['by_key']['margin']['value'].endswith('%'))

    def test_access_is_limited_to_the_director(self):
        clerk = self._user('td_clerk', ['base.group_user', 'sales_team.group_sale_salesman', 'stock.group_stock_manager'])
        with self.assertRaises(AccessError):
            self.env['td.mebli.dashboard'].with_user(clerk).get_data()
        director = self._user('td_director', ['base.group_user', 'td_mebli_dashboard.group_td_mebli_director'])
        self.assertEqual(len(self.env['td.mebli.dashboard'].with_user(director).get_data()['cards']), len(KEYS))

    def test_load_counts_only_the_work_of_the_next_7_days(self):
        """The load tile divides the open work planned to start within 7 days by the weekly hours, not the whole queue."""
        dashboard = self.env['td.mebli.dashboard']
        start, end = dashboard._week()
        self.assertEqual((end - start).days, 7)
        card = dashboard._card_load(self.env)
        drill_ids = set(card['drill']['ids'])
        week = self.env['mrp.workorder'].search([('date_start', '!=', False), ('date_start', '<', end),
                                                 ('state', 'not in', ('done', 'cancel'))])
        self.assertEqual(drill_ids, set(week.ids))
        later = self.env['mrp.workorder'].search([('date_start', '>=', end)])
        self.assertFalse(drill_ids & set(later.ids))
        self.assertTrue(start <= fields.Datetime.now() < end)
