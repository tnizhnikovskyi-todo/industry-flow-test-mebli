from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDashboard(TransactionCase):
    def test_get_data_on_empty_database(self):
        data = self.env['td.mebli.dashboard'].get_data()
        cards = data['cards']
        self.assertEqual(set(cards), {'revenue', 'margin', 'launch', 'load', 'cutting', 'plan_fact'})
        self.assertEqual(cards['margin']['value'].split()[-1], '%')
        for card in cards.values():
            self.assertTrue(self.env.ref(card['action'].replace('.', '.', 1)))

    def _user(self, login, groups):
        return self.env['res.users'].with_context(no_reset_password=True).create({
            'name': login, 'login': login,
            'group_ids': [(6, 0, [self.env.ref(g).id for g in groups])]})

    def test_access_is_limited_to_the_director(self):
        clerk = self._user('td_clerk', ['base.group_user', 'sales_team.group_sale_salesman', 'stock.group_stock_manager'])
        with self.assertRaises(AccessError):
            self.env['td.mebli.dashboard'].with_user(clerk).get_data()
        director = self._user('td_director', ['base.group_user', 'td_mebli_dashboard.group_td_mebli_director'])
        self.assertIn('revenue', self.env['td.mebli.dashboard'].with_user(director).get_data()['cards'])

    def test_margin_drilldown_needs_no_view_access(self):
        """The drill-down of the margin card must work for a user who cannot read ir.ui.view: the id of the list view comes from the server."""
        owner = self._user('td_owner', ['base.group_user', 'sales_team.group_sale_manager', 'td_mebli_dashboard.group_td_mebli_director'])
        with self.assertRaises(AccessError):
            self.env['ir.model.data'].with_user(owner).check_object_reference('td_mebli_sale', 'sale_order_td_low_margin_list')
        card = self.env['td.mebli.dashboard'].with_user(owner).get_data()['cards']['margin']
        view = self.env.ref('td_mebli_sale.sale_order_td_low_margin_list')
        self.assertEqual(card['low_view_id'], view.id)
        kanban = self.env.ref('td_mebli_sale.sale_order_td_low_margin_kanban')
        self.assertEqual(card['low_kanban_id'], kanban.id)  # на малому екрані drill-down відкривається канбаном (маржа видна)
        self.assertEqual(kanban.type, 'kanban')
        self.assertIsInstance(card['low_ids'], list)
