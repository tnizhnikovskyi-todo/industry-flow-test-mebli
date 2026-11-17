from odoo.tests import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestEeLookSwitch(TransactionCase):
    """A-17 №17 (owner remark 2026-11-16): one switch — system parameter td_home_menu.ee_look, on by default."""

    def test_on_by_default_and_switch_off(self):
        Param = self.env['ir.config_parameter'].sudo()
        Param.search([('key', '=', 'td_home_menu.ee_look')]).unlink()
        self.assertTrue(self.env['ir.http']._td_ee_look())
        Param.set_param('td_home_menu.ee_look', 'False')
        self.assertFalse(self.env['ir.http']._td_ee_look())
        Param.set_param('td_home_menu.ee_look', 'True')
        self.assertTrue(self.env['ir.http']._td_ee_look())


@tagged('post_install', '-at_install')
class TestChatterResizeTour(HttpCase):
    browser_size = '1920x1080'  # the chatter is beside the form only on wide screens (mail: SIZES.XXL)

    def test_chatter_resize_tour(self):
        if 'message_ids' not in self.env['res.partner']._fields:
            self.skipTest("mail is not installed: no chatter")
        partner = self.env['res.partner'].create({'name': 'A-17 chatter'})
        self.start_tour(f'/odoo/action-base.action_partner_form/{partner.id}', 'td_chatter_resize_tour', login='admin')
