from datetime import timedelta

from odoo import fields
from odoo.tests import tagged

from odoo.addons.td_mebli_sale.tests.common import TdMebliSaleCommon

ACTIVITY = 'td_mebli_notify.mail_activity_type_td_forecast_shift'


@tagged('post_install', '-at_install')
class TestNotify(TdMebliSaleCommon):
    """F-50 activity on the forecast shift, F-51 letters to the customer, F-64 morning briefing."""

    def _activities(self, order):
        return self.env['mail.activity'].search([('res_model', '=', 'sale.order'), ('res_id', '=', order.id),
                                                 ('activity_type_id', '=', self.env.ref(ACTIVITY).id)])

    def test_activity_created_once_updated_and_closed(self):
        order = self._make_order()
        order.action_confirm()
        start = fields.Date.context_today(order, order.date_order)
        # promised in the past: any forecast is later
        order.commitment_date = fields.Datetime.to_datetime(start - timedelta(days=10))
        activity = self._activities(order)
        self.assertEqual(len(activity), 1, "the forecast passed the promised date")
        self.assertEqual(activity.user_id, order.user_id)
        order._td_sync_forecast_activity()
        order._td_sync_forecast_activity()
        self.assertEqual(len(self._activities(order)), 1, "no duplicate")
        before = self._activities(order).summary
        order.commitment_date = fields.Datetime.to_datetime(start - timedelta(days=5))
        self.assertNotEqual(self._activities(order).summary, before, "the shift is updated")
        self.assertIn('%s' % order.td_delay_days, self._activities(order).summary)
        order.commitment_date = fields.Datetime.to_datetime(start + timedelta(days=365))
        self.assertFalse(self._activities(order), "the forecast came back: the activity is done")

    def test_new_date_letter_opens_the_composer(self):
        order = self._make_order()
        action = order.action_td_notify_new_date()
        self.assertEqual(action['res_model'], 'mail.compose.message')
        self.assertEqual(action['context']['default_template_id'], self.env.ref('td_mebli_notify.mail_template_td_new_date').id)

    def test_letter_queued_for_the_customer(self):
        self.partner.email = 'buyer@example.com'
        order = self._make_order()
        order.action_confirm()
        order._td_post_letter('td_mebli_notify.mail_template_td_payment_reminder')
        template = self.env.ref('td_mebli_notify.mail_template_td_payment_reminder')
        subject = template._render_field('subject', order.ids, compute_lang=True)[order.id]
        messages = order.message_ids.filtered(lambda m: m.subject == subject)
        self.assertEqual(len(messages), 1)
        self.assertIn(self.partner, messages.partner_ids, "the customer gets the letter (queued by the mail queue)")
        self.assertTrue(self.env['mail.mail'].search([('mail_message_id', '=', messages.id)]))

    def test_activity_done_is_not_reopened_for_the_same_shift(self):
        order = self._make_order()
        order.action_confirm()
        start = fields.Date.context_today(order, order.date_order)
        order.commitment_date = fields.Datetime.to_datetime(start - timedelta(days=10))
        shift = order.td_delay_days
        self._activities(order).action_feedback(feedback='Called the customer')
        self.assertFalse(self._activities(order))
        self.env['sale.order']._cron_td_forecast_activity()
        self.assertFalse(self._activities(order), "marked «Done»: the cron does not open it again for the same shift")
        self.assertEqual(order.td_forecast_shift_done, shift)
        order.commitment_date = fields.Datetime.to_datetime(start - timedelta(days=15))
        self.assertGreater(order.td_delay_days, shift)
        self.assertEqual(len(self._activities(order)), 1, "the shift grew: a new activity")
        order.commitment_date = fields.Datetime.to_datetime(start + timedelta(days=365))
        self.assertFalse(order.td_forecast_shift_done, "the forecast came back: the handled shift is reset")

    def test_install_reminder_tomorrow(self):
        self.partner.email = 'buyer@example.com'
        project = self.env['project.project'].create({'name': 'Installation', 'allow_billable': True})
        service = self.env['product.product'].create({'name': 'Installation', 'type': 'service', 'list_price': 100,
                                                      'service_tracking': 'task_global_project', 'project_id': project.id})
        order = self.env['sale.order'].create({'partner_id': self.partner.id,
                                               'order_line': [(0, 0, {'product_id': service.id})]})
        order.action_confirm()
        task = order.tasks_ids[:1]
        task.date_deadline = fields.Datetime.now() + timedelta(days=1)
        result = self.env['project.task']._cron_td_customer_reminders()
        self.assertGreaterEqual(result['install'], 1)
        self.assertTrue(task.message_ids.filtered(lambda m: order.name in (m.subject or '')))
        self.assertTrue(task.td_install_reminded_for)
        again = self.env['project.task']._cron_td_customer_reminders()
        self.assertEqual(again, {'install': 0, 'payment': 0, 'no_email': 0}, "once per visit date: the next run sends nothing")
        if result['payment']:
            payment = self.env.ref('td_mebli_notify.mail_template_td_payment_reminder')
            subject = payment._render_field('subject', order.ids, compute_lang=True)[order.id]
            self.assertEqual(len(order.message_ids.filtered(lambda m: m.subject == subject)), 1)

    def _owner(self, login, companies=None):
        companies = companies or self.env.company
        return self.env['res.users'].with_context(no_reset_password=True).create({
            'name': login, 'login': login, 'email': '%s@example.com' % login,
            'company_id': companies[:1].id, 'company_ids': [(6, 0, companies.ids)],
            'group_ids': [(6, 0, [self.env.ref('td_mebli_dashboard.group_td_mebli_director').id,
                                  self.env.ref('base.group_user').id])]})

    def _briefings(self, partner):
        return self.env['mail.message'].sudo().search([('partner_ids', 'in', partner.ids),
                                                        ('body', 'ilike', 'td_briefing')])

    def test_briefing(self):
        data = self.env['td.mebli.dashboard']._td_briefing_data()
        for key in ('at_risk', 'overdue', 'due_after_act', 'due_before', 'downtime'):
            self.assertIn(key, data)
        owner = self._owner('td_owner')
        employee = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Worker', 'login': 'td_worker', 'email': 'worker@example.com',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.assertGreaterEqual(self.env['res.partner']._cron_td_morning_briefing(), 1)
        message = self._briefings(owner.partner_id)
        self.assertEqual(len(message), 1, "one personal briefing")
        self.assertFalse(message.model, "a personal notification, not a message in the chatter of a record")
        self.assertFalse(owner.partner_id.message_ids.filtered(lambda m: 'td_briefing' in (m.body or '')))
        self.assertTrue(self.env['mail.message'].with_user(owner).search([('id', '=', message.id)]),
                        "the owner reads his briefing")
        self.assertFalse(self.env['mail.message'].with_user(employee).search([('id', '=', message.id)]),
                         "an ordinary employee does not see the briefing")
        self.assertNotIn(employee.partner_id, message.partner_ids)

    def test_briefing_only_companies_of_the_owner(self):
        order = self._make_order()
        order.action_confirm()
        start = fields.Date.context_today(order, order.date_order)
        order.commitment_date = fields.Datetime.to_datetime(start - timedelta(days=10))
        self.assertGreater(order.td_delay_days, 0)
        other = self.env['res.company'].create({'name': 'Second factory'})
        own = self._owner('td_owner_a')
        foreign = self._owner('td_owner_b', other)
        both = self._owner('td_owner_ab', self.env.company | other)
        notify = self.env['res.partner']
        template = self.env.ref('td_mebli_notify.mail_template_td_briefing')
        for owner in (own, foreign, both):
            notify._td_send_briefing(template, owner)
        self.assertIn(order.name, self._briefings(own.partner_id).body)
        self.assertNotIn(order.name, self._briefings(foreign.partner_id).body,
                         "the owner of the second company does not see the orders of the first one")
        self.assertIn(order.name, self._briefings(both.partner_id).body)

    def test_briefing_counts_visits_of_a_project_without_company(self):
        project = self.env['project.project'].create({'name': 'Installation', 'allow_billable': True, 'company_id': False})
        service = self.env['product.product'].create({'name': 'Installation', 'type': 'service', 'list_price': 100,
                                                      'service_tracking': 'task_global_project', 'project_id': project.id})
        order = self.env['sale.order'].create({'partner_id': self.partner.id,
                                               'order_line': [(0, 0, {'product_id': service.id})]})
        order.action_confirm()
        task = order.tasks_ids[:1]
        task.date_deadline = fields.Datetime.now() + timedelta(days=2)
        self.assertFalse(task.company_id, "the task of a project without a company")
        if order.td_pay_missing <= 0:
            self.skipTest("the order is not due before the installation in this setup")
        owner = self._owner('td_owner_visits')
        data = self.env['td.mebli.dashboard'].with_user(owner).with_context(
            allowed_company_ids=owner.company_ids.ids)._td_briefing_data()
        self.assertGreaterEqual(data['due_before_count'], 1, "the visit counts by the company of its order")
