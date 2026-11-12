from datetime import datetime, time, timedelta

import pytz

from odoo import api, fields, models


class TdMebliDashboard(models.AbstractModel):
    _inherit = 'td.mebli.dashboard'

    @api.model
    def _td_briefing_data(self):
        """Position 32 (F-64): the morning briefing of the owner, from the data of the package by fixed rules (no AI):
        orders at risk with the reason, overdue manufacturing orders, money to receive (A1), downtime of the sections
        yesterday (standard loss reasons of the work centers)."""
        _ = self.env._
        env = self.env
        now = fields.Datetime.now()
        reasons = dict(env['sale.order']._fields['td_delay_reason']._description_selection(env))
        risk = env['sale.order'].search([('state', '=', 'sale'), ('commitment_date', '!=', False)]).filtered(
            lambda o: o.td_delay_days > 0 and o.delivery_status != 'full').sorted(lambda o: -o.td_delay_days)
        at_risk = [{'name': o.name, 'customer': o.partner_id.name, 'days': o.td_delay_days,
                    'reason': reasons.get(o.td_delay_reason, '') + (f': {o.td_late_item}' if o.td_late_item else '')}
                   for o in risk]
        overdue = env['mrp.production'].search([('state', 'in', ('confirmed', 'progress', 'to_close')),
                                                ('date_deadline', '<', now)], order='date_deadline')
        overdue_rows = [{'name': p.name, 'origin': p.origin or '', 'days': (now - p.date_deadline).days} for p in overdue]
        acts = env['td.mebli.install.act'].search([('kind', '=', 'final'), ('state', '=', 'signed')])
        after_act = acts.order_id.filtered(lambda o: o.td_dash_due > 0.5)
        visits = env['project.task'].search([('sale_order_id.state', '=', 'sale'), ('state', 'not in', ('1_done', '1_canceled')),
                                             ('date_deadline', '>=', now), ('date_deadline', '<', now + timedelta(days=7))])
        before = visits.sale_order_id.filtered(lambda o: o.td_pay_missing > 0)
        # yesterday: the calendar day before today in the time zone of the user
        tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'Europe/Kyiv')
        today = tz.localize(datetime.combine(fields.Datetime.now().replace(tzinfo=pytz.utc).astimezone(tz).date(), time.min)).astimezone(pytz.utc).replace(tzinfo=None)
        losses = env['mrp.workcenter.productivity'].search([('loss_type', '!=', 'productive'),
                                                            ('date_start', '>=', today - timedelta(days=1)),
                                                            ('date_start', '<', today)])
        downtime = {}
        for row in losses:
            key = (row.workcenter_id.name, row.loss_id.name)
            downtime[key] = downtime.get(key, 0.0) + row.duration
        return {
            'at_risk': at_risk, 'overdue': overdue_rows,
            'due_after_act': self._money(sum(after_act.mapped('td_dash_due'))), 'due_after_act_count': len(after_act),
            'due_before': self._money(sum(before.mapped('td_pay_missing'))), 'due_before_count': len(before),
            'downtime': [{'center': c, 'reason': r, 'hours': self._num(m / 60.0)} for (c, r), m in sorted(downtime.items())],
        }


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _cron_td_morning_briefing(self):
        """The briefing goes to the owners (group «Director» of the dashboard): a standard template posted to their
        contact, the owner reads it in the inbox of Odoo or by e-mail (standard notification preference)."""
        group = self.env.ref('td_mebli_dashboard.group_td_mebli_director', raise_if_not_found=False)
        users = group.sudo().all_user_ids.filtered(lambda u: u.active and not u.share) if group else self.env['res.users']
        users = users.filtered(lambda u: u.id != self.env.ref('base.user_admin').id) or users
        partners = users.partner_id
        for partner in partners:
            partner.with_context(lang=partner.lang).message_post_with_source(
                'td_mebli_notify.mail_template_td_briefing', subtype_xmlid='mail.mt_comment')
        return len(partners)
