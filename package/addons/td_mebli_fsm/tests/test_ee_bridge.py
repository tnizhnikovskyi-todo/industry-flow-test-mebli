from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'td_mebli_ee')
class TestEeBridge(TransactionCase):
    """AC-128: runs only on Odoo Enterprise (the bridge is not installed on Community, AC-130)."""

    def test_ac_128_bridge_installed_with_its_enterprise_app(self):
        Module = self.env['ir.module.module']
        self.assertEqual(Module.search([('name', '=', 'td_mebli_fsm')]).state, 'installed')
        self.assertEqual(Module.search([('name', '=', 'industry_fsm')]).state, 'installed')

    def test_ac_128_enterprise_fields_and_hidden_screens(self):
        """The fields of the Enterprise models the bridge relies on (assumptions until ВП-4) and the hidden screens."""
        fields = self.env['project.task']._fields
        for field in ['is_fsm', 'user_ids', 'sale_order_id']:
            self.assertIn(field, fields, 'assumption of tr/ee-bridges.md: project.task.%s exists on Enterprise' % field)
        fields = self.env['project.project']._fields
        for field in ['is_fsm']:
            self.assertIn(field, fields, 'assumption of tr/ee-bridges.md: project.project.%s exists on Enterprise' % field)
        self.assertEqual(self.env.ref('td_mebli_install.td_mebli_install_calendar_menu').group_ids, self.env.ref('td_mebli_fsm.group_td_old_screens'),
                         'the td_ screen is hidden by a group')

    def test_ac_128_act_on_the_field_service_task(self):
        self.assertIn('td_act_ids', self.env['project.task']._fields)
        self.assertIn('td_is_fsm', self.env['td.mebli.install.act']._fields)
