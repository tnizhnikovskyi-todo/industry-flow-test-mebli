from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'td_mebli_ee')
class TestEeBridge(TransactionCase):
    """AC-127: runs only on Odoo Enterprise (the bridge is not installed on Community, AC-130)."""

    def test_ac_127_bridge_installed_with_its_enterprise_app(self):
        Module = self.env['ir.module.module']
        self.assertEqual(Module.search([('name', '=', 'td_mebli_quality')]).state, 'installed')
        self.assertEqual(Module.search([('name', '=', 'quality_control')]).state, 'installed')

    def test_ac_127_enterprise_fields_and_hidden_screens(self):
        """The fields of the Enterprise models the bridge relies on (assumptions until ВП-4) and the hidden screens."""
        fields = self.env['quality.point']._fields
        for field in ['title', 'operation_id', 'product_ids', 'picking_type_ids', 'company_id']:
            self.assertIn(field, fields, 'assumption of tr/ee-bridges.md: quality.point.%s exists on Enterprise' % field)
        fields = self.env['quality.check']._fields
        for field in ['quality_state', 'point_id', 'company_id']:
            self.assertIn(field, fields, 'assumption of tr/ee-bridges.md: quality.check.%s exists on Enterprise' % field)
        self.assertEqual(self.env.ref('td_mebli_shop.td_mebli_quality_check_menu').group_ids, self.env.ref('td_mebli_quality.group_td_old_screens'),
                         'the td_ screen is hidden by a group')
        self.assertNotIn(self.env.ref('td_mebli_base.group_feature_quality'),
                         self.env.ref('base.group_user').implied_ids, 'the function of box B is replaced')

    def test_ac_127_quality_points_from_the_operations(self):
        operation = self.env['mrp.routing.workcenter'].search([('td_quality_point', '!=', False)], limit=1)
        if not operation:
            self.skipTest('no operation with a quality step in this database')
        self.env['quality.point'].search([('operation_id', '=', operation.id)]).unlink()
        points = operation._td_sync_quality_points()
        self.assertEqual(points.title, operation.td_quality_point)
        self.assertFalse(operation._td_sync_quality_points(), "not doubled")
        self.assertIsInstance(self.env['quality.check']._td_nonconformity_count(), int)
