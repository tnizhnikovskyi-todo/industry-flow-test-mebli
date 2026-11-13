from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'td_mebli_ee')
class TestEeBridge(TransactionCase):
    """AC-126: runs only on Odoo Enterprise (the bridge is not installed on Community, AC-130)."""

    def test_ac_126_bridge_installed_with_its_enterprise_app(self):
        Module = self.env['ir.module.module']
        self.assertEqual(Module.search([('name', '=', 'td_mebli_shopfloor')]).state, 'installed')
        self.assertEqual(Module.search([('name', '=', 'mrp_workorder')]).state, 'installed')

    def test_ac_126_enterprise_fields_and_hidden_screens(self):
        """The fields of the Enterprise models the bridge relies on (assumptions until ВП-4) and the hidden screens."""
        fields = self.env['mrp.workorder']._fields
        for field in ['production_id', 'workcenter_id', 'employee_ids']:
            self.assertIn(field, fields, 'assumption of tr/ee-bridges.md: mrp.workorder.%s exists on Enterprise' % field)
        fields = self.env['mrp.workcenter.productivity']._fields
        for field in ['loss_id', 'employee_id']:
            self.assertIn(field, fields, 'assumption of tr/ee-bridges.md: mrp.workcenter.productivity.%s exists on Enterprise' % field)
        self.assertEqual(self.env.ref('td_mebli_shop.td_mebli_tablet_menu').group_ids, self.env.ref('td_mebli_shopfloor.group_td_old_screens'),
                         'the td_ screen is hidden by a group')
        self.assertNotIn(self.env.ref('td_mebli_base.group_feature_kiosk'),
                         self.env.ref('base.group_user').implied_ids, 'the function of box B is replaced')

    def test_ac_126_work_order_shows_the_parts(self):
        self.assertIn('td_part_ids', self.env['mrp.workorder']._fields)
        self.assertTrue(self.env['mrp.workcenter.productivity.loss'].search_count([]), "the pause reasons are standard")
