from collections import defaultdict
from datetime import datetime, time, timedelta

import pytz

from odoo import api, fields, models


class ProjectTask(models.Model):
    """Position 17 (F-58): the day plan of an installation crew — the standard visit tasks of the orders (date of the
    visit, crew in the assignees) printed or opened on the phone: time, address, order, places to load, payment to
    collect. Nothing is entered here."""
    _inherit = 'project.task'

    td_address = fields.Char(string='Address', compute='_compute_td_day')
    td_places = fields.Char(string='Places to Load', compute='_compute_td_day')

    def _compute_td_day(self):
        for task in self:
            order = task.sale_order_id
            task.td_address = task._td_address(order.partner_shipping_id or task.partner_id) or False
            task.td_places = str(order.td_kit_places) if order and order.td_kit_places else False

    @api.model
    def _td_address(self, partner):
        return ', '.join(filter(None, [partner.street, partner.street2, partner.city]))

    @api.model
    def _td_factory_tz(self):
        """The day of the crew is the day of the factory: the time zone of the company working calendar."""
        return pytz.timezone(self.env.company.resource_calendar_id.tz or self.env.context.get('tz') or 'Europe/Kyiv')

    def _td_local(self, value):
        tz = self._td_factory_tz()
        return pytz.utc.localize(value).astimezone(tz) if value else False

    def _td_day_plan_groups(self):
        """[(day, crew names, [rows])] sorted by day and time."""
        groups = defaultdict(list)
        for task in self.filtered('date_deadline').sorted('date_deadline'):
            local = self._td_local(task.date_deadline)
            order = task.sale_order_id
            places = [f"{place}: {', '.join(lines.mapped('item'))}" for place, lines in order._td_kit_by_place()] \
                if order else []
            crew = ', '.join(task.user_ids.mapped('name'))
            groups[(local.date(), crew)].append({
                'time': local.strftime('%H:%M'), 'task': task.name, 'order': order.name or '',
                'customer': order.partner_id.name or task.partner_id.name or '',
                'phone': order.partner_id.phone or '',
                'address': task._td_address(order.partner_shipping_id or task.partner_id),
                'places': places, 'kit_missing': order.td_kit_missing if order else 0,
                'pay_missing': order.td_pay_missing if order else 0.0, 'currency': order.currency_id,
            })
        return [(day, crew, rows) for (day, crew), rows in sorted(groups.items())]

    @api.model
    def action_td_my_day(self):
        """The visits of the current user today (the crew on the phone)."""
        tz = self._td_factory_tz()
        today = fields.Datetime.now().replace(tzinfo=pytz.utc).astimezone(tz).date()
        start = tz.localize(datetime.combine(today, time.min)).astimezone(pytz.utc).replace(tzinfo=None)
        action = self.env['ir.actions.act_window']._for_xml_id('td_mebli_install.td_mebli_install_day_action')
        action['domain'] = [('sale_order_id', '!=', False), ('user_ids', 'in', self.env.user.ids),
                            ('date_deadline', '>=', start), ('date_deadline', '<', start + timedelta(days=1))]
        return action


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _td_day_plan_groups(self, days=7):
        """The day plan of a crew member: his visits from today for `days` days, a page per day."""
        self.ensure_one()
        tz = self.env['project.task']._td_factory_tz()
        start = tz.localize(datetime.combine(fields.Datetime.now().replace(tzinfo=pytz.utc).astimezone(tz).date(), time.min)).astimezone(pytz.utc).replace(tzinfo=None)
        tasks = self.env['project.task'].search([('sale_order_id', '!=', False), ('user_ids', 'in', self.ids),
                                                 ('state', 'not in', ('1_done', '1_canceled')),
                                                 ('date_deadline', '>=', start),
                                                 ('date_deadline', '<', start + timedelta(days=days))])
        return tasks._td_day_plan_groups()
