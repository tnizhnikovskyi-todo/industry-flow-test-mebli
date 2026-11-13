from datetime import datetime, time, timedelta

import pytz

from odoo import api, fields, models

PAYMENT_DAYS = 3  # the payment before the installation is reminded this many days before the visit


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _td_post_letter(self, template_xmlid):
        """Post a standard template letter in the chatter of each record (subtype «Discussions»: the customer of the
        template gets it by e-mail, queued by the standard mail queue). The callers decide whether the letter is due
        (the reminders keep on the visit the date of the visit already reminded); the subject is not used as a key."""
        template = self.env.ref(template_xmlid)
        for record in self:
            record.message_post_with_source(template, subtype_xmlid='mail.mt_comment')
        return self


class ProjectTask(models.Model):
    _inherit = 'project.task'

    td_install_reminded_for = fields.Date(
        string='Installation Reminder Sent for', copy=False, readonly=True,
        help="The date of the visit the customer was reminded of (once per visit date; a moved visit is reminded again).")
    td_payment_reminded_for = fields.Date(
        string='Payment Reminder Sent for', copy=False, readonly=True,
        help="The date of the visit for which the payment before the installation was reminded (once per visit date).")

    @api.model
    def _td_visits_between(self, start, end):
        return self.search([('sale_order_id.state', '=', 'sale'), ('date_deadline', '>=', start), ('date_deadline', '<', end),
                            ('state', 'not in', ('1_done', '1_canceled'))])

    @api.model
    def _td_reminder_tz(self):
        # the cron runs as a technical user: the day of the customers is the day of the company calendar
        return pytz.timezone(self.env.company.resource_calendar_id.tz or self.env.context.get('tz')
                             or self.env.user.tz or 'Europe/Kyiv')

    @api.model
    def _cron_td_customer_reminders(self):
        """Position 2 (F-51): letters to the customers — the installation tomorrow; the payment before the installation
        when the visit is in the next days and the order is not paid as the payment terms ask (A1). Each letter once per
        visit date (the key is kept on the visit, not the subject of the letter): the payment is reminded once, not
        every morning until the visit; a visit moved to another date is reminded again. The measurement reminder is
        the standard e-mail alarm of the calendar meeting (td_mebli_measure)."""
        tz = self._td_reminder_tz()
        today = fields.Datetime.now().replace(tzinfo=pytz.utc).astimezone(tz).date()
        to_utc = lambda day: tz.localize(datetime.combine(day, time.min)).astimezone(pytz.utc).replace(tzinfo=None)  # noqa: E731
        visit_day = lambda task: pytz.utc.localize(task.date_deadline).astimezone(tz).date()  # noqa: E731
        tomorrow = self._td_visits_between(to_utc(today + timedelta(days=1)), to_utc(today + timedelta(days=2)))
        tomorrow = tomorrow.filtered(lambda t: t.td_install_reminded_for != visit_day(t))
        tomorrow._td_post_letter('td_mebli_notify.mail_template_td_install_reminder')
        for task in tomorrow:
            task.sudo().td_install_reminded_for = visit_day(task)
        soon = self._td_visits_between(to_utc(today), to_utc(today + timedelta(days=PAYMENT_DAYS + 1)))
        soon = soon.filtered(lambda t: t.td_payment_reminded_for != visit_day(t) and t.sale_order_id.td_pay_missing > 0)
        orders = soon.sale_order_id
        orders._td_post_letter('td_mebli_notify.mail_template_td_payment_reminder')
        for task in soon:
            task.sudo().td_payment_reminded_for = visit_day(task)
        return {'install': len(tomorrow), 'payment': len(orders)}
