from datetime import datetime, time

import pytz

from odoo import api, fields, models
from odoo.exceptions import AccessError


class TdMebliDashboard(models.AbstractModel):
    _inherit = 'td.mebli.dashboard'

    @api.model
    def get_shop_board(self):
        """Position 39 (F-65): the board of the shop floor on a TV, from the data of the tablet (standard work orders and
        their time lines): done in the shift, in work now, orders at risk, sections behind the plan. Read only."""
        user = self.env.user
        if not (self.env.su or user.has_group('mrp.group_mrp_user') or user.has_group('base.group_system')):
            raise AccessError(self.env._("The shop floor board is available to the users of Manufacturing."))
        _ = self.env._
        env = self.sudo().with_company(self.env.company).env
        # the board hangs in the shop: the time zone of the company working calendar
        tz = pytz.timezone(self.env.company.resource_calendar_id.tz or self.env.context.get('tz') or 'Europe/Kyiv')
        now = fields.Datetime.now()
        shift_start = tz.localize(datetime.combine(fields.Datetime.now().replace(tzinfo=pytz.utc).astimezone(tz).date(), time.min)).astimezone(pytz.utc).replace(tzinfo=None)
        Workorder = env['mrp.workorder']
        # done in the shift: the operations finished whose time lines (tablet, standard log) ended in this shift
        shift_lines = env['mrp.workcenter.productivity'].search([('date_end', '>=', shift_start),
                                                                 ('workorder_id.state', '=', 'done')])
        done = shift_lines.workorder_id
        working = Workorder.search([('state', '=', 'progress')])
        behind = Workorder.search([('state', 'in', ('ready', 'progress', 'blocked', 'pending', 'waiting')),
                                   ('date_finished', '!=', False), ('date_finished', '<', now)])
        centers = []
        for center in env['mrp.workcenter'].search([], order='sequence, id'):
            c_done = done.filtered(lambda w: w.workcenter_id == center)
            c_behind = behind.filtered(lambda w: w.workcenter_id == center)
            if not (c_done or c_behind or working.filtered(lambda w: w.workcenter_id == center)):
                continue
            centers.append({
                'name': center.name, 'done': len(c_done),
                'done_hours': self._num(sum(shift_lines.filtered(lambda l: l.workcenter_id == center).mapped('duration')) / 60.0),
                'working': len(working.filtered(lambda w: w.workcenter_id == center)),
                'behind': len(c_behind), 'behind_hours': self._num(sum(c_behind.mapped('td_expected_hours'))),
            })
        people = []
        for workorder in working:
            open_line = workorder.time_ids.filtered(lambda t: not t.date_end)[:1]
            people.append({'center': workorder.workcenter_id.name, 'operation': workorder.name,
                           'order': workorder.production_id.origin or workorder.production_id.name,
                           'worker': open_line.td_employee_id.name or ''})
        risk = env['sale.order'].search([('state', '=', 'sale'), ('commitment_date', '!=', False)]).filtered(
            lambda o: o.td_delay_days > 0 and o.delivery_status != 'full').sorted(lambda o: -o.td_delay_days)
        return {
            'title': _("Shop Floor"),
            'clock': pytz.utc.localize(now).astimezone(tz).strftime('%d.%m.%Y %H:%M'),
            'done': len(done), 'done_hours': self._num(sum(shift_lines.mapped('duration')) / 60.0),
            'working': len(working), 'behind': len(behind), 'risk_count': len(risk),
            'centers': centers, 'people': people[:8],
            'risk': [{'name': o.name, 'customer': o.partner_id.name, 'days': o.td_delay_days} for o in risk[:6]],
        }
