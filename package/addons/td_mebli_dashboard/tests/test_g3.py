from odoo.tests import TransactionCase, tagged

from .test_dashboard import KEYS


@tagged('post_install', '-at_install')
class TestDashboardG3(TransactionCase):

    def _director(self, login, extra=()):
        groups = ['base.group_user', 'td_mebli_dashboard.group_td_mebli_director', *extra]
        return self.env['res.users'].with_context(no_reset_password=True).create({
            'name': login, 'login': login, 'group_ids': [(6, 0, [self.env.ref(g).id for g in groups])]})

    def test_ac_121_twelfth_card_of_the_quality_in_box_b(self):
        env = self.env
        a_box = self._director('td_g3_dir_a')
        self.assertEqual({card['key'] for card in env['td.mebli.dashboard'].with_user(a_box).get_data()['cards']}, KEYS)
        b_box = self._director('td_g3_dir_b', ['td_mebli_base.group_feature_quality'])
        center = env['mrp.workcenter'].create({'name': 'Edge banding'})
        product = env['product.product'].create({'name': 'Shelf', 'is_storable': True})
        bom = env['mrp.bom'].create({'product_tmpl_id': product.product_tmpl_id.id, 'operation_ids': [
            (0, 0, {'name': 'Edge', 'workcenter_id': center.id, 'time_cycle_manual': 10})]})
        production = env['mrp.production'].create({'product_id': product.id, 'bom_id': bom.id})
        production.action_confirm()
        Check = env['td.mebli.quality.check']
        failed = Check.create({'workorder_id': production.workorder_ids.id, 'name': 'Edge glue', 'result': 'fail'})
        Check.create({'workorder_id': production.workorder_ids.id, 'name': 'Size', 'result': 'pass'})
        scrap = Check.create({'workorder_id': production.workorder_ids.id, 'name': 'Scratched panel',  # AC-073 scrap
                             'result': 'fail', 'kind': 'scrap'})
        data = env['td.mebli.dashboard'].with_user(b_box).get_data()
        self.assertEqual(len(data['cards']), 12)
        card = data['by_key']['quality']
        self.assertEqual(card['value'], '2')  # the failed quality step and the scrap
        self.assertEqual(set(card['drill']['ids']), {failed.id, scrap.id})  # the drill-down is the records counted
        self.assertEqual(card['drill']['res_model'], 'td.mebli.quality.check')
        self.assertIn('Edge banding', [row['name'] for row in card['rows']])

    def test_ac_123_empty_data(self):
        """A new company without orders: every card shows 0 or «No data», nothing is divided by zero."""
        env = self.env
        env['res.lang']._activate_lang('uk_UA')
        company = env['res.company'].create({'name': 'New furniture factory'})
        director = self._director('td_g3_dir_empty', ['td_mebli_base.group_feature_quality'])
        director.write({'company_ids': [(4, company.id)], 'company_id': company.id})
        dashboard = env['td.mebli.dashboard'].with_user(director).with_company(company)
        data = dashboard.get_data()
        self.assertEqual(len(data['cards']), 12)
        for card in data['cards']:
            self.assertEqual(card['drill']['ids'], [], card['key'])
            value = card.get('value')
            if value is not None:
                self.assertTrue(value == 'No data' or value.startswith('0'), (card['key'], value))
        self.assertEqual(data['by_key']['on_time']['value'], 'No data')
        self.assertEqual(data['by_key']['margin']['value'], 'No data')
        uk = dashboard.with_context(lang='uk_UA').get_data()
        self.assertEqual(uk['by_key']['claims']['value'], 'Немає даних')

    def test_stuck_days_of_the_company(self):
        """VP-10: the stuck card reads the days of the company (td_mebli_base), not a constant."""
        self.env.company.td_stuck_days = 12
        card = self.env['td.mebli.dashboard']._card_stuck(self.env, self.env.company)
        self.assertIn('12', card['target'])

    def test_ac_122_menu_and_finance_of_the_director(self):
        env = self.env
        director_group = env.ref('td_mebli_dashboard.group_td_mebli_director')
        self.assertIn(env.ref('td_mebli_base.group_finance'), director_group.all_implied_ids)
        menu = env.ref('td_mebli_dashboard.menu_dashboard_root')
        manager = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Sales manager', 'login': 'td_g3_sm',
            'group_ids': [(6, 0, [env.ref('sales_team.group_sale_manager').id, env.ref('mrp.group_mrp_manager').id])]})
        self.assertNotIn(menu.id, env['ir.ui.menu'].with_user(manager)._visible_menu_ids())
        self.assertIn(menu.id, env['ir.ui.menu'].with_user(self._director('td_g3_dir_menu'))._visible_menu_ids())

    def test_shop_board_menu_only_in_box_b(self):
        env = self.env
        menu = env.ref('td_mebli_dashboard.menu_shop_board')
        self.assertEqual(menu.group_ids, env.ref('td_mebli_base.group_feature_shop_board'))
