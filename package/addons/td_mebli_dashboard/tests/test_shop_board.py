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
