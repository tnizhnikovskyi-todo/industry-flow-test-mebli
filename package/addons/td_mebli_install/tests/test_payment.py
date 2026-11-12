from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

PHOTO = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='


@tagged('post_install', '-at_install')
class TestPaymentControl(TransactionCase):
    """A1 (F-22, PAIN-17): the payment schedule is the standard payment terms; the control before the installation reads
    the invoices of the order; the parameter of the company warns (default) or blocks the start and the act."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.term = env['account.payment.term'].create({'name': '50/40/10', 'line_ids': [
            (0, 0, {'value': 'percent', 'value_amount': 50.0, 'nb_days': 0, 'td_milestone': 'order'}),
            (0, 0, {'value': 'percent', 'value_amount': 40.0, 'nb_days': 14, 'td_milestone': 'install'}),
            (0, 0, {'value': 'percent', 'value_amount': 10.0, 'nb_days': 30, 'td_milestone': 'act'})]})
        cls.partner = env['res.partner'].create({'name': 'Customer'})
        project = env['project.project'].create({'name': 'Installation', 'allow_billable': True})
        cls.service = env['product.product'].create({
            'name': 'Kitchen installation', 'list_price': 10000.0, 'type': 'service', 'taxes_id': [(5, 0, 0)],
            'invoice_policy': 'order', 'service_tracking': 'task_global_project', 'project_id': project.id})

    def _order(self):
        order = self.env['sale.order'].create({'partner_id': self.partner.id, 'payment_term_id': self.term.id,
                                               'order_line': [(0, 0, {'product_id': self.service.id})]})
        order.action_confirm()
        return order

    def _pay(self, order, percent):
        """A standard down payment invoice of the order, posted and paid."""
        wizard = self.env['sale.advance.payment.inv'].with_context(active_model='sale.order', active_ids=order.ids).create(
            {'advance_payment_method': 'percentage', 'amount': percent})
        wizard.create_invoices()
        invoice = order.invoice_ids.filtered(lambda m: m.state == 'draft')
        invoice.action_post()
        self.env['account.payment.register'].with_context(active_model='account.move', active_ids=invoice.ids).create(
            {'amount': invoice.amount_residual})._create_payments()

    def test_due_before_installation_from_the_terms(self):
        order = self._order()
        self.assertAlmostEqual(order.td_pay_before_install, 9000.0)  # 50 % + 40 %, not the 10 % after the act
        self.assertFalse(order.td_pay_ok)
        self._pay(order, 50)
        order.invalidate_recordset()
        self.assertAlmostEqual(order.td_pay_received, 5000.0)
        self.assertAlmostEqual(order.td_pay_missing, 4000.0)
        self.assertFalse(order.tasks_ids.td_pay_ok)
        self._pay(order, 40)
        order.invalidate_recordset()
        self.assertTrue(order.td_pay_ok)
        self.assertTrue(order.tasks_ids.td_pay_ok)

    def test_terms_without_milestones_ask_the_whole_amount(self):
        order = self._order()
        order.payment_term_id = self.env.ref('account.account_payment_term_immediate')
        self.assertAlmostEqual(order.td_pay_before_install, order.amount_total)

    def test_warn_by_default_block_by_parameter(self):
        order = self._order()
        task = order.tasks_ids
        # warn (default): the crew starts, the act is signed, the visit and the act show the missing amount
        action = task.action_td_start_install()
        act = task.td_act_ids
        self.assertEqual(act.kind, 'final')
        self.assertEqual(task.state, '01_in_progress')
        self.assertTrue(action)
        self.assertFalse(act.pay_ok)
        act.write({'signature': PHOTO, 'signed_by': 'Customer'})
        act.action_sign()
        self.assertEqual(act.state, 'signed')
        # block: «Start the installation» and «Sign the act» are refused until the payment
        self.env['ir.config_parameter'].sudo().set_param('td_mebli_install.payment_control', 'block')
        second = self._order()
        with self.assertRaises(UserError):
            second.tasks_ids.action_td_start_install()
        with self.assertRaises(UserError):
            self.env['td.mebli.install.act'].create({'task_id': second.tasks_ids.id, 'kind': 'final'})
        self._pay(second, 90)
        second.tasks_ids.action_td_start_install()
        self.assertEqual(len(second.tasks_ids.td_act_ids), 1)

    def test_settings_parameter(self):
        settings = self.env['res.config.settings'].create({'td_mebli_payment_control': 'block'})
        settings.execute()
        self.assertEqual(self.env['ir.config_parameter'].sudo().get_param('td_mebli_install.payment_control'), 'block')

    def test_act_report_renders(self):
        order = self._order()
        act = self.env['td.mebli.install.act'].create({'task_id': order.tasks_ids.id, 'kind': 'final',
                                                       'signature': PHOTO, 'signed_by': 'Customer',
                                                       'defect_ids': [(0, 0, {'name': 'Gap on the left door'})]})
        html, kind = self.env['ir.actions.report']._render_qweb_html('td_mebli_install.report_install_act', act.ids)
        self.assertEqual(kind, 'html')
        self.assertIn(act.name.encode(), html)
        self.assertIn(b'Gap on the left door', html)
        self.assertNotIn(b'ToDo', html)  # the document carries the brand of the factory, not of the integrator
