from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged

from odoo.addons.td_mebli_sale.tests.common import TdMebliSaleCommon


@tagged('post_install', '-at_install')
class TestG1Notify(TdMebliSaleCommon):
    """A-11 G1: AC-030 letters by template, AC-031 payment reminder (VP-07), AC-124/AC-125 morning briefing."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        env['res.lang']._activate_lang('uk_UA')
        env['ir.module.module']._load_module_terms(['td_mebli_notify'], ['uk_UA'], overwrite=True)
        cls.project = env['project.project'].create({'name': 'Монтажі', 'allow_billable': True})
        cls.service = env['product.product'].create({'name': 'Монтаж', 'type': 'service', 'list_price': 100,
                                                     'service_tracking': 'task_global_project',
                                                     'project_id': cls.project.id})
        cls.term = env['account.payment.term'].create({'name': '50/50', 'line_ids': [
            (0, 0, {'value': 'percent', 'value_amount': 50.0, 'nb_days': 0, 'td_milestone': 'order'}),
            (0, 0, {'value': 'percent', 'value_amount': 50.0, 'nb_days': 0, 'td_milestone': 'install'})]})

    def _visit(self, days):
        order = self.env['sale.order'].create({'partner_id': self.partner.id, 'payment_term_id': self.term.id,
                                               'order_line': [(0, 0, {'product_id': self.service.id})]})
        order.action_confirm()
        task = order.tasks_ids[:1]
        task.date_deadline = fields.Datetime.now() + timedelta(days=days, hours=2)
        return order, task

    def _payment_letters(self, order):
        template = self.env.ref('td_mebli_notify.mail_template_td_payment_reminder')
        subject = template._render_field('subject', order.ids, compute_lang=True)[order.id]
        return order.message_ids.filtered(lambda m: m.subject == subject)

    def test_ac_030_letters_by_template(self):
        env = self.env
        self.partner.write({'email': 'buyer@example.com', 'street': 'вул. Вигадана, 1', 'city': 'Київ'})
        lead = env['crm.lead'].create({'name': 'Кухня', 'type': 'opportunity', 'partner_id': self.partner.id})
        start = fields.Datetime.now().replace(microsecond=0) + timedelta(days=3)
        event = env['calendar.event'].create({
            'name': 'Замір', 'start': start, 'stop': start + timedelta(hours=2), 'opportunity_id': lead.id,
            'location': 'вул. Вигадана, 1, Київ', 'user_id': env.user.id,
            'partner_ids': [(6, 0, (env.user.partner_id | self.partner).ids)]})
        booking = env.ref('td_mebli_notify.mail_template_td_measure_booking')
        body = booking._render_field('body_html', event.ids)[event.id]
        self.assertIn('вул. Вигадана, 1, Київ', body)
        self.assertIn(start.strftime('%d.%m.%Y'), body)
        # the standard composer of the meeting with the template: the letter goes to the chatter of the record
        composer = env['mail.compose.message'].with_context(
            default_model='calendar.event', default_res_ids=event.ids, default_template_id=booking.id,
            default_composition_mode='comment').create({})
        self.assertIn('Вигадана', composer.body)
        composer._action_send_mail()
        self.assertTrue(event.message_ids.filtered(lambda m: 'Вигадана' in (m.body or '')))
        # «Date of the installation»: the date, the amount and the address of the order
        order, task = self._visit(5)
        install = env.ref('td_mebli_notify.mail_template_td_install_date')
        body = install._render_field('body_html', task.ids)[task.id]
        self.assertIn(order.name, body)
        self.assertIn('Вигадана', body)
        names = {t.with_context(lang='uk_UA').name for t in (booking, install, env.ref(
            'td_mebli_notify.mail_template_td_payment_reminder'), env.ref('td_mebli_notify.mail_template_td_new_date'))}
        self.assertEqual(len(names), 4)

    def test_ac_031_reminder_days_by_the_company(self):
        self.partner.email = 'buyer@example.com'
        self.env.company.td_pay_reminder_days = 2
        order, task = self._visit(2)
        far, far_task = self._visit(4)
        self.assertGreater(order.td_pay_missing, 0)
        result = self.env['project.task']._cron_td_customer_reminders()
        self.assertEqual(len(self._payment_letters(order)), 1, "the visit in 2 days (the parameter): one letter")
        self.assertFalse(self._payment_letters(far), "the visit in 4 days: not yet")
        self.assertGreaterEqual(result['payment'], 1)
        self.env['project.task']._cron_td_customer_reminders()
        self.assertEqual(len(self._payment_letters(order)), 1, "once")
        self.env.company.td_pay_reminder_days = 5
        self.env['project.task']._cron_td_customer_reminders()
        self.assertEqual(len(self._payment_letters(far)), 1, "the parameter 5: the farther visit is reminded too")

    def test_ac_031_no_email(self):
        self.partner.email = False
        self.env.company.td_pay_reminder_days = 2
        order, _task = self._visit(1)
        result = self.env['project.task']._cron_td_customer_reminders()
        self.assertEqual(result['no_email'], 1)
        self.assertFalse(self._payment_letters(order))
        notes = order.message_ids.filtered(lambda m: 'Reminder not sent: no email' in (m.body or ''))
        self.assertEqual(len(notes), 1)
        self.assertTrue(order.activity_ids.filtered(lambda a: a.user_id == order.user_id))
        text = self.env['project.task'].with_context(lang='uk_UA').env._("Reminder not sent: no email")
        self.assertEqual(text, "Нагадування не надіслано: немає email")
        self.env['project.task']._cron_td_customer_reminders()
        self.assertEqual(len(order.message_ids.filtered(lambda m: 'Reminder not sent' in (m.body or ''))), 1, "once")

    def test_ac_124_briefing_sections(self):
        order = self._make_order()
        order.action_confirm()
        order.sudo().write({'td_stage_date': fields.Datetime.now() - timedelta(days=9)})
        self.env.company.td_stuck_days = 5
        data = self.env['td.mebli.dashboard']._td_briefing_data()
        for key in ('at_risk', 'claims', 'due_after_act', 'due_before', 'stuck', 'overdue', 'downtime'):
            self.assertIn(key, data)
        self.assertIn(order.name, [row['name'] for row in data['stuck']])
        self.assertFalse(data['nothing'])
        template = self.env.ref('td_mebli_notify.mail_template_td_briefing')
        body = template._render_field('body_html', self.env.user.partner_id.ids,
                                      add_context={'briefing': data})[self.env.user.partner_id.id]
        self.assertIn(order.name, body)
        self.assertIn('Stuck orders', body)
        cron = self.env.ref('td_mebli_notify.ir_cron_td_morning_briefing')
        self.assertEqual(cron.interval_type, 'days')

    def test_ac_125_nothing_to_report(self):
        empty = {'nothing': True, 'at_risk': [], 'claims': [], 'stuck': [], 'overdue': [], 'downtime': [],
                 'due_after_act': '0', 'due_after_act_count': 0, 'due_before': '0', 'due_before_count': 0}
        template = self.env.ref('td_mebli_notify.mail_template_td_briefing')
        partner = self.env.user.partner_id
        body = template._render_field('body_html', partner.ids, add_context={'briefing': empty})[partner.id]
        self.assertIn('No deviations', body)
        for section in ('Orders at risk', 'Overdue claims', 'Money to receive', 'Stuck orders', 'Downtime'):
            self.assertNotIn(section, body)
        partner.lang = 'uk_UA'
        body = template.with_context(lang='uk_UA')._render_field('body_html', partner.ids, compute_lang=True,
                                                                  add_context={'briefing': empty})[partner.id]
        self.assertIn('Відхилень немає', body)
        # the real data of an empty database gives «nothing»
        with patch.object(type(self.env['td.mebli.dashboard']), '_td_briefing_data', lambda self: empty):
            owner = self.env['res.users'].with_context(no_reset_password=True).create({
                'name': 'Власник', 'login': 'td_g1_owner', 'email': 'owner@example.com',
                'group_ids': [(6, 0, [self.env.ref('td_mebli_dashboard.group_td_mebli_director').id,
                                      self.env.ref('base.group_user').id])]})
            self.env['res.partner']._td_send_briefing(template, owner)
        message = self.env['mail.message'].sudo().search([('partner_ids', 'in', owner.partner_id.ids)], limit=1)
        self.assertIn('No deviations', message.body)
