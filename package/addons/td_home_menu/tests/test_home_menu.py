from odoo.tests import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHomeMenuFlag(TransactionCase):

    def test_active_on_community(self):
        self.assertTrue(self.env['ir.http']._td_home_menu_active())

    def test_inactive_with_enterprise(self):
        """With web_enterprise installed the module changes nothing (the JS patches read this flag)."""
        module = self.env['ir.module.module'].search([('name', '=', 'web_enterprise')])
        if module:
            module.state = 'installed'
        else:
            self.env['ir.module.module'].create({'name': 'web_enterprise', 'state': 'installed'})
        self.assertFalse(self.env['ir.http']._td_home_menu_active())


@tagged('post_install', '-at_install')
class TestHomeMenuTour(HttpCase):

    def test_home_menu_tour(self):
        self.start_tour('/odoo', 'td_home_menu_tour', login='admin')
