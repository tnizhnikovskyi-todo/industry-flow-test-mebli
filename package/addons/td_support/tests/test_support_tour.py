from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestSupportTour(HttpCase):

    def test_support_dialog_tour(self):
        self.env['ir.config_parameter'].sudo().set_param('td_support.email', 'support@example.com')
        self.start_tour('/odoo/action-base.action_res_users', 'td_support_tour', login='admin')
        request = self.env['td.support.request'].search([('subject', '=', 'Tour: cannot print the order')])
        self.assertEqual(len(request), 1)
        self.assertEqual(request.state, 'sent')
        self.assertTrue(request.mail_id.subject.startswith('[ToDo-support]['))
