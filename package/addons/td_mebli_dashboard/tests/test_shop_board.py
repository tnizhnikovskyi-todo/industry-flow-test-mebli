from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestShopBoard(TransactionCase):
    """F-65: the shop floor board reads the tablet data, for the users of Manufacturing only."""

    def test_board_figures(self):
        center = self.env['mrp.workcenter'].create({'name': 'Saw'})
        product = self.env['product.product'].create({'name': 'Shelf', 'is_storable': True})
        bom = self.env['mrp.bom'].create({'product_tmpl_id': product.product_tmpl_id.id, 'operation_ids': [
            (0, 0, {'name': 'Cut', 'workcenter_id': center.id, 'time_cycle_manual': 30})]})
        production = self.env['mrp.production'].create({'product_id': product.id, 'bom_id': bom.id})
        production.action_confirm()
        production.workorder_ids.button_start()
        data = self.env['td.mebli.dashboard'].get_shop_board()
        self.assertEqual(data['working'], 1)
        self.assertIn('Saw', [c['name'] for c in data['centers']])
        production.workorder_ids.button_finish()
        data = self.env['td.mebli.dashboard'].get_shop_board()
        self.assertEqual(data['done'], 1)
        for key in ('risk', 'behind', 'clock', 'people'):
            self.assertIn(key, data)

    def test_board_needs_manufacturing(self):
        user = self.env['res.users'].with_context(no_reset_password=True).create(
            {'name': 'Seller', 'login': 'td_seller', 'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        with self.assertRaises(AccessError):
            self.env['td.mebli.dashboard'].with_user(user).get_shop_board()

    def test_board_only_selected_companies(self):
        other = self.env['res.company'].create({'name': 'Second factory'})
        center = self.env['mrp.workcenter'].create({'name': 'Edge B', 'company_id': other.id,
                                                 'resource_calendar_id': other.resource_calendar_id.id})
        product = self.env['product.product'].create({'name': 'Door B', 'is_storable': True, 'company_id': other.id})
        bom = self.env['mrp.bom'].create({'product_tmpl_id': product.product_tmpl_id.id, 'company_id': other.id,
                                          'operation_ids': [(0, 0, {'name': 'Edge', 'workcenter_id': center.id,
                                                                    'time_cycle_manual': 30})]})
        production = self.env['mrp.production'].with_company(other).create(
            {'product_id': product.id, 'bom_id': bom.id, 'company_id': other.id})
        production.action_confirm()
        production.workorder_ids.button_start()
        main = self.env.company
        user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Master', 'login': 'td_master', 'company_id': main.id, 'company_ids': [(6, 0, (main | other).ids)],
            'group_ids': [(6, 0, [self.env.ref('mrp.group_mrp_user').id])]})
        board = self.env['td.mebli.dashboard'].with_user(user)
        data = board.with_context(allowed_company_ids=main.ids).get_shop_board()
        self.assertEqual(data['working'], 0, "the work of the second company is not on the board of the first one")
        self.assertNotIn('Edge B', [c['name'] for c in data['centers']])
        data = board.with_context(allowed_company_ids=other.ids).get_shop_board()
        self.assertEqual(data['working'], 1)
        self.assertIn('Edge B', [c['name'] for c in data['centers']])
