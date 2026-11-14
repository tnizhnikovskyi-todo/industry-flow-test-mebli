from odoo.tests import Form, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestA117Install(TransactionCase):
    """A-11-7: the defects of A-16 in td_mebli_install, through the form of the order and the act (Form)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        env.company.td_install_in_price = False
        cls.term = env['account.payment.term'].create({'name': '50/40/10', 'line_ids': [
            (0, 0, {'value': 'percent', 'value_amount': 50.0, 'nb_days': 0, 'td_milestone': 'order'}),
            (0, 0, {'value': 'percent', 'value_amount': 40.0, 'nb_days': 14, 'td_milestone': 'install'}),
            (0, 0, {'value': 'percent', 'value_amount': 10.0, 'nb_days': 30, 'td_milestone': 'act'})]})
        cls.partner = env['res.partner'].create({'name': 'Customer'})
        project = env['project.project'].create({'name': 'Installation', 'allow_billable': True})
        cls.service = env['product.product'].create({
            'name': 'Kitchen installation', 'list_price': 10000.0, 'type': 'service', 'taxes_id': [(5, 0, 0)],
            'invoice_policy': 'order', 'service_tracking': 'task_global_project', 'project_id': project.id})
        cls.salesman = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Salon', 'login': 'td_a117_install_salon',
            'group_ids': [(6, 0, [cls.env.ref('sales_team.group_sale_salesman').id])]})

    def test_d02_new_order_saved_from_the_full_form(self):
        """The form of the order with the payment banner (td_stage in the arch): a salesperson saves a new order."""
        arch = self.env['sale.order'].with_user(self.salesman).get_views([(False, 'form')])['views']['form']['arch']
        self.assertIn('name="td_stage"', arch)
        with Form(self.env['sale.order'].with_user(self.salesman)) as form:
            form.partner_id = self.partner
            form.payment_term_id = self.term
            with form.order_line.new() as line:
                line.product_id = self.service
        self.assertEqual(form.record.td_stage, 'quote')
        form.record.with_user(self.salesman).write({'note': 'saved again'})

    def test_d05_due_and_received_in_the_quotation_form(self):
        """AC-019: «Due before installation» and «Received» in the form as soon as the terms with milestones are chosen."""
        with Form(self.env['sale.order'].with_user(self.salesman)) as form:
            form.partner_id = self.partner
            with form.order_line.new() as line:
                line.product_id = self.service
            form.payment_term_id = self.term
            self.assertTrue(form.td_pay_has_milestones)
            self.assertAlmostEqual(form.td_pay_before_install, 9000.0)  # 50 % + 40 % of 10 000
            self.assertIn('40 %', str(form.td_pay_schedule_html))
        order = form.record
        self.assertTrue(order.td_pay_ok, "a quotation is not «missing» the payment")
        arch = order.with_user(self.salesman).get_views([(False, 'form')])['views']['form']['arch']
        for field in ('td_pay_before_install', 'td_pay_received', 'td_pay_schedule_html'):
            self.assertIn(f'name="{field}"', arch)
        order.action_confirm()
        self.assertAlmostEqual(order.td_pay_missing, 9000.0)

    def test_d13_act_in_ukrainian(self):
        """The default checklist, the statuses and the title of the act are Ukrainian for a Ukrainian user."""
        env = self.env
        env['res.lang']._activate_lang('uk_UA')
        env.company.td_act_checklist = False
        order = env['sale.order'].create({'partner_id': self.partner.id, 'payment_term_id': self.term.id,
                                          'order_line': [(0, 0, {'product_id': self.service.id})]})
        order.action_confirm()
        task = order.tasks_ids[:1]
        act = env['td.mebli.install.act'].with_context(lang='uk_UA').create({'task_id': task.id})
        self.assertNotIn('Fronts adjusted', act.checklist)
        labels = dict(act._fields['state']._description_selection(act.with_context(lang='uk_UA').env))
        self.assertNotEqual(labels['draft'], 'Draft')
        self.assertNotEqual(labels['signed'], 'Signed')
        arch = act.with_context(lang='uk_UA').get_views([(False, 'form')])['views']['form']['arch']
        self.assertNotIn('Installation Act', arch)
