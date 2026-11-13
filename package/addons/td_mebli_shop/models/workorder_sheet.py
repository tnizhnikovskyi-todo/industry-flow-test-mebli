from datetime import timedelta

from odoo import fields, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _td_sheet_parts(self):
        """AC-133: parts of the paper work order sheet — the same codes as the labels of the order (labels.py)."""
        self.ensure_one()
        report = self.env['ir.actions.report']
        return [{'code': row['code'], 'item': row['item'], 'size': row['size'], 'material': row['material'],
                 'qty': row['qty'], 'qr': report._td_qr_data_uri(row['code'], size=80)}
                for row in self._td_label_rows_by_part()]

    def _td_label_rows_by_part(self):
        self.ensure_one()
        return [{'code': f"{self.name}-{index:02d}", 'item': part.name,
                 'size': f"{int(part.length_mm)} × {int(part.width_mm)}", 'material': part.material_id.name,
                 'qty': part.qty * self.product_qty}
                for index, part in enumerate(self.bom_id.td_part_ids, start=1)]


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    def action_td_done_backdated(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'res_model': 'td.mebli.workorder.backdate', 'view_mode': 'form',
                'target': 'new', 'name': self.env._("Done Afterwards"),
                'context': {'default_workorder_id': self.id}}


class TdMebliWorkorderBackdate(models.TransientModel):
    """AC-133: after a power cut the master marks the paper work order sheet «Done» with the real interval and the
    reason: a time line on that interval, the work order done, the reason in the chatter of the manufacturing order."""
    _name = 'td.mebli.workorder.backdate'
    _description = 'Work Order Done Afterwards'

    workorder_id = fields.Many2one('mrp.workorder', string='Work Order', required=True)
    employee_id = fields.Many2one('hr.employee', string='Worker')
    date_start = fields.Datetime(string='Started', required=True,
                                 default=lambda self: fields.Datetime.now() - timedelta(hours=1))
    date_end = fields.Datetime(string='Finished', required=True, default=fields.Datetime.now)
    reason = fields.Char(string='Reason', required=True)

    def action_confirm(self):
        self.ensure_one()
        if self.date_end > fields.Datetime.now():
            raise UserError(self.env._("The end date cannot be in the future"))
        if self.date_start >= self.date_end:
            raise UserError(self.env._("The start must be before the end."))
        workorder = self.workorder_id
        if workorder.state in ('done', 'cancel'):
            raise UserError(self.env._("%s is already closed.", workorder.display_name))
        minutes = (self.date_end - self.date_start).total_seconds() / 60.0
        vals = workorder._prepare_timeline_vals(minutes, self.date_start, self.date_end)
        vals['description'] = self.reason
        line = self.env['mrp.workcenter.productivity'].create(vals)
        if self.employee_id:
            line.sudo().td_employee_id = self.employee_id
        workorder.button_finish()
        workorder.with_context(bypass_duration_calculation=True).write({
            'date_finished': self.date_end, 'date_start': min(workorder.date_start or self.date_start, self.date_start)})
        workorder.production_id.message_post(body=self.env._(
            "%(wo)s done afterwards: %(start)s – %(end)s. Reason: %(reason)s",
            wo=workorder.name, start=fields.Datetime.context_timestamp(self, self.date_start).strftime('%d.%m.%Y %H:%M'),
            end=fields.Datetime.context_timestamp(self, self.date_end).strftime('%d.%m.%Y %H:%M'), reason=self.reason))
        return {'type': 'ir.actions.act_window_close'}
