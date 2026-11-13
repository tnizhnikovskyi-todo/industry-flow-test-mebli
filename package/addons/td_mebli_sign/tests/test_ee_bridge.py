from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'td_mebli_ee')
class TestEeBridge(TransactionCase):
    """AC-129: runs only on Odoo Enterprise (the bridge is not installed on Community, AC-130)."""

    def test_ac_129_bridge_installed_with_its_enterprise_app(self):
        Module = self.env['ir.module.module']
        self.assertEqual(Module.search([('name', '=', 'td_mebli_sign')]).state, 'installed')
        self.assertEqual(Module.search([('name', '=', 'sign')]).state, 'installed')

    def test_ac_129_enterprise_fields_and_hidden_screens(self):
        """The fields of the Enterprise models the bridge relies on (assumptions until ВП-4) and the hidden screens."""
        fields = self.env['sign.template']._fields
        for field in ['attachment_id']:
            self.assertIn(field, fields, 'assumption of tr/ee-bridges.md: sign.template.%s exists on Enterprise' % field)
        fields = self.env['sign.request']._fields
        for field in ['state', 'reference_doc', 'completed_document', 'template_id']:
            self.assertIn(field, fields, 'assumption of tr/ee-bridges.md: sign.request.%s exists on Enterprise' % field)

    def test_ac_129_send_and_get_back(self):
        self.assertTrue(hasattr(self.env['sale.order'], 'action_td_send_sign'))
        self.assertTrue(hasattr(self.env['td.mebli.install.act'], 'action_td_send_sign'))
        self.assertIn('sign.send.request', self.env)
