from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'td_mebli_ee')
class TestEeBridge(TransactionCase):
    """AC-113: runs only on Odoo Enterprise (the bridge is not installed on Community, AC-130)."""

    def test_ac_113_bridge_installed_with_its_enterprise_app(self):
        Module = self.env['ir.module.module']
        self.assertEqual(Module.search([('name', '=', 'td_mebli_helpdesk')]).state, 'installed')
        self.assertEqual(Module.search([('name', '=', 'helpdesk')]).state, 'installed')

    def test_ac_113_enterprise_fields_and_hidden_screens(self):
        """The fields of the Enterprise models the bridge relies on (assumptions until ВП-4) and the hidden screens."""
        fields = self.env['helpdesk.ticket']._fields
        for field in ['partner_id', 'team_id', 'name', 'company_id']:
            self.assertIn(field, fields, 'assumption of tr/ee-bridges.md: helpdesk.ticket.%s exists on Enterprise' % field)
        self.assertEqual(self.env.ref('td_mebli_claim.td_mebli_claim_menu').group_ids, self.env.ref('td_mebli_helpdesk.group_td_old_screens'),
                         'the td_ screen is hidden by a group')

    def test_ac_113_ticket_creates_the_claim(self):
        partner = self.env['res.partner'].create({'name': 'Customer EE'})
        order = self.env['sale.order'].create({'partner_id': partner.id})
        ticket = self.env['helpdesk.ticket'].create({'name': 'Door is scratched', 'partner_id': partner.id,
                                                     'td_sale_order_id': order.id})
        ticket.action_td_create_claim()
        self.assertEqual(ticket.td_repair_id.td_claim_order_id, order)
