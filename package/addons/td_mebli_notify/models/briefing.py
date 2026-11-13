from datetime import datetime, time, timedelta

import pytz

from odoo import api, fields, models


class TdMebliDashboard(models.AbstractModel):
    _inherit = 'td.mebli.dashboard'

    @api.model
    def _td_briefing_data(self):
        """Position 32 (F-64): the morning briefing of the owner, from the data of the package by fixed rules (no AI):
        orders at risk with the reason, overdue manufacturing orders, money to receive (A1), downtime of the sections
        yesterday (standard loss reasons of the work centers).

        Like the dashboard, the figures are read from the whole factory (sudo, the director is not a user of every
        application), but only of the companies of the reader: every search is limited to ``self.env.companies`` (the
        cron calls it as each owner with his allowed companies)."""
        companies = self.env.companies
        env = self.sudo().env
        now = fields.Datetime.now()
        in_companies = [('company_id', 'in', companies.ids)]
        reasons = dict(env['sale.order']._fields['td_delay_reason']._description_selection(env))
        risk = env['sale.order'].search([('state', '=', 'sale'), ('commitment_date', '!=', False)] + in_companies).filtered(
            lambda o: o.td_delay_days > 0 and o.delivery_status != 'full').sorted(lambda o: -o.td_delay_days)
        at_risk = [{'name': o.name, 'customer': o.partner_id.name, 'days': o.td_delay_days,
                    'reason': reasons.get(o.td_delay_reason, '') + (f': {o.td_late_item}' if o.td_late_item else '')}
                   for o in risk]
        overdue = env['mrp.production'].search([('state', 'in', ('confirmed', 'progress', 'to_close')),
                                                ('date_deadline', '<', now)] + in_companies, order='date_deadline')
        overdue_rows = [{'name': p.name, 'origin': p.origin or '', 'days': (now - p.date_deadline).days} for p in overdue]
        acts = env['td.mebli.install.act'].search([('kind', '=', 'final'), ('state', '=', 'signed'),
                                                   ('order_id.company_id', 'in', companies.ids)])
        after_act = acts.order_id.filtered(lambda o: o.td_dash_due > 0.5)
        visits = env['project.task'].search([('sale_order_id.state', '=', 'sale'), ('state', 'not in', ('1_done', '1_canceled')),
                                             ('date_deadline', '>=', now), ('date_deadline', '<', now + timedelta(days=7)),
                                             # the visit is of the company of its order (a task of a project without a
                                             # company has no company of its own)
                                             ('sale_order_id.company_id', 'in', companies.ids)])
        before = visits.sale_order_id.filtered(lambda o: o.td_pay_missing > 0)
        # yesterday: the calendar day before today in the time zone of the user
        tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'Europe/Kyiv')
        today = tz.localize(datetime.combine(fields.Datetime.now().replace(tzinfo=pytz.utc).astimezone(tz).date(), time.min)).astimezone(pytz.utc).replace(tzinfo=None)
        losses = env['mrp.workcenter.productivity'].search([('loss_type', '!=', 'productive'),
                                                            ('date_start', '>=', today - timedelta(days=1)),
                                                            ('date_start', '<', today)] + in_companies)
        # AC-124: overdue claims (VP-13 — the claim module computes «overdue» by the parameter of the company)
        claims = env['repair.order'].search([('td_claim_order_id', '!=', False), ('state', 'not in', ('done', 'cancel'))]
                                            + in_companies).filtered('td_overdue')
        claim_rows = [{'name': c.name, 'customer': c.partner_id.name or '', 'days': c.td_days_open} for c in claims]
        # AC-124, AC-067: stuck orders (VP-10, the parameter of each company)
        stuck = env['sale.order'].with_context(allowed_company_ids=companies.ids).search(
            [('td_is_stuck', '=', True)] + in_companies, order='td_stage_date')
        stuck_rows = [{'name': o.name, 'customer': o.partner_id.name, 'days': (now - o.td_stage_date).days}
                      for o in stuck]
        downtime = {}
        for row in losses:
            key = (row.workcenter_id.name, row.loss_id.name)
            downtime[key] = downtime.get(key, 0.0) + row.duration
        downtime_rows = [{'center': c, 'reason': r, 'hours': self._num(m / 60.0)}
                         for (c, r), m in sorted(downtime.items())]
        nothing = not (at_risk or overdue_rows or claim_rows or stuck_rows or after_act or before or downtime_rows)
        return {
            'nothing': nothing, 'claims': claim_rows, 'stuck': stuck_rows,
            'at_risk': at_risk, 'overdue': overdue_rows,
            'due_after_act': self._money(sum(after_act.mapped('td_dash_due'))), 'due_after_act_count': len(after_act),
            'due_before': self._money(sum(before.mapped('td_pay_missing'))), 'due_before_count': len(before),
            'downtime': downtime_rows,
        }


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _cron_td_morning_briefing(self):
        """The briefing goes to the owners (group «Director» of the dashboard), each one separately: the figures are
        read for his allowed companies, the standard template is rendered for him and sent by ``message_notify`` — a
        personal notification (Inbox or e-mail by his notification preference, the mail queue), not a message in the
        chatter of a record: nobody else reads it."""
        group = self.env.ref('td_mebli_dashboard.group_td_mebli_director', raise_if_not_found=False)
        users = group.sudo().all_user_ids.filtered(lambda u: u.active and not u.share) if group else self.env['res.users']
        users = users.filtered(lambda u: u.id != self.env.ref('base.user_admin').id) or users
        template = self.env.ref('td_mebli_notify.mail_template_td_briefing')
        for owner in users:
            self._td_send_briefing(template, owner)
        return len(users)

    @api.model
    def _td_send_briefing(self, template, owner):
        partner = owner.partner_id
        # the day of the briefing in the time zone of the owner (else of his company calendar), not in UTC
        tz = owner.tz or owner.company_id.resource_calendar_id.tz or 'Europe/Kyiv'
        today = fields.Datetime.now().replace(tzinfo=pytz.utc).astimezone(pytz.timezone(tz)).date()
        data = self.env['td.mebli.dashboard'].with_user(owner).with_company(owner.company_id).with_context(
            allowed_company_ids=owner.company_ids.ids, tz=tz)._td_briefing_data()
        template = template.with_context(lang=partner.lang or owner.lang, td_today=today)
        subject = template._render_field('subject', partner.ids)[partner.id]
        body = template._render_field('body_html', partner.ids, add_context={'briefing': data})[partner.id]
        return self.env['res.partner'].with_context(lang=partner.lang).message_notify(
            partner_ids=partner.ids, subject=subject, body=body,
            email_from=owner.company_id.email_formatted or None,
            email_layout_xmlid='mail.mail_notification_light')
