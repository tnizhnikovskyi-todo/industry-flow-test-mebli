from datetime import datetime, time, timedelta

import pytz

from odoo import api, fields, models

PAYMENT_DAYS = 3  # the payment before the installation is reminded this many days before the visit


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _td_post_letter(self, template_xmlid):
        """Post a standard template letter in the chatter of each record (subtype «Discussions»: the customer of the
        template gets it by e-mail, queued by the standard mail queue). Once a day per record and template: a letter
        with the same subject posted today is not repeated."""
        template = self.env.ref(template_xmlid)
        tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'Europe/Kyiv')
        today = tz.localize(datetime.combine(fields.Datetime.now().replace(tzinfo=pytz.utc).astimezone(tz).date(), time.min)).astimezone(pytz.utc).replace(tzinfo=None)
        posted = self.browse()
        for record in self:
            subject = template._render_field('subject', record.ids)[record.id]
            if self.env['mail.message'].sudo().search_count([
                    ('model', '=', record._name), ('res_id', '=', record.id), ('subject', '=', subject),
                    ('date', '>=', today)], limit=1):
                continue
            record.message_post_with_source(template, subtype_xmlid='mail.mt_comment')
            posted |= record
        return posted


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.model
    def _td_visits_between(self, start, end):
        return self.search([('sale_order_id.state', '=', 'sale'), ('date_deadline', '>=', start), ('date_deadline', '<', end),
                            ('state', 'not in', ('1_done', '1_canceled'))])

    @api.model
    def _cron_td_customer_reminders(self):
        """Position 2 (F-51): letters to the customers — the installation tomorrow; the payment before the installation
        when the visit is in the next days and the order is not paid as the payment terms ask (A1). The measurement
        reminder is the standard e-mail alarm of the calendar meeting (td_mebli_measure)."""
        tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'Europe/Kyiv')
        today = fields.Datetime.now().replace(tzinfo=pytz.utc).astimezone(tz).date()
        to_utc = lambda day: tz.localize(datetime.combine(day, time.min)).astimezone(pytz.utc).replace(tzinfo=None)  # noqa: E731
        tomorrow = self._td_visits_between(to_utc(today + timedelta(days=1)), to_utc(today + timedelta(days=2)))
        tomorrow._td_post_letter('td_mebli_notify.mail_template_td_install_reminder')
        soon = self._td_visits_between(to_utc(today), to_utc(today + timedelta(days=PAYMENT_DAYS + 1)))
        orders = soon.sale_order_id.filtered(lambda o: o.td_pay_missing > 0)
        orders._td_post_letter('td_mebli_notify.mail_template_td_payment_reminder')
        return {'install': len(tomorrow), 'payment': len(orders)}
