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

    def test_letter_posted_once_a_day(self):
        self.partner.email = 'buyer@example.com'
        order = self._make_order()
        order.action_confirm()
        order._td_post_letter('td_mebli_notify.mail_template_td_payment_reminder')
        order._td_post_letter('td_mebli_notify.mail_template_td_payment_reminder')
        template = self.env.ref('td_mebli_notify.mail_template_td_payment_reminder')
        subject = template._render_field('subject', order.ids)[order.id]
        messages = order.message_ids.filtered(lambda m: m.subject == subject)
        self.assertEqual(len(messages), 1)
        self.assertIn(self.partner, messages.partner_ids, "the customer gets the letter (queued by the mail queue)")
        self.assertTrue(self.env['mail.mail'].search([('mail_message_id', '=', messages.id)]))

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

    def test_briefing(self):
        data = self.env['td.mebli.dashboard']._td_briefing_data()
        for key in ('at_risk', 'overdue', 'due_after_act', 'due_before', 'downtime'):
            self.assertIn(key, data)
        owner = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Owner', 'login': 'td_owner', 'email': 'owner@example.com',
            'group_ids': [(6, 0, [self.env.ref('td_mebli_dashboard.group_td_mebli_director').id,
                                  self.env.ref('base.group_user').id])]})
        self.assertGreaterEqual(self.env['res.partner']._cron_td_morning_briefing(), 1)
        message = owner.partner_id.message_ids[:1]
        self.assertIn('td_briefing', message.body)
