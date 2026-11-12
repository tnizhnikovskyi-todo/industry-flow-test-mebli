from odoo import api, fields, models
from odoo.exceptions import UserError


class TdMebliKiosk(models.TransientModel):
    _name = 'td.mebli.kiosk'
    _description = 'Shop Floor Tablet: PIN of the Worker'

    workorder_id = fields.Many2one('mrp.workorder', string='Work Order', required=True)
    action = fields.Selection([('start', 'Taken'), ('pause', 'Pause'), ('done', 'Done'), ('quality', 'Quality Step')],
                              string='Action', required=True, default='start')
    employee_id = fields.Many2one('hr.employee', string='Worker', required=True)
    pin = fields.Char(string='PIN')
    loss_id = fields.Many2one('mrp.workcenter.productivity.loss', string='Pause Reason',
                              domain="[('loss_type', 'in', ('availability', 'quality', 'performance'))]")
    quality_point = fields.Char(related='workorder_id.td_quality_point')
    result = fields.Selection([('pass', 'Passed'), ('fail', 'Failed')], string='Result', default='pass')
    photo = fields.Image(string='Photo', max_width=1024, max_height=1024)
    note = fields.Char(string='Note')

    def _check_pin(self):
        employee = self.employee_id.sudo()  # the PIN is an HR field; the tablet user only compares it
        if not employee.pin:
            raise UserError(self.env._("%s has no PIN: ask the shop manager to set it in the employee card.", employee.name))
        if (self.pin or '') != employee.pin:
            raise UserError(self.env._("Wrong PIN."))

    def action_confirm(self):
        self.ensure_one()
        self._check_pin()
        workorder = self.workorder_id
        before = workorder.time_ids
        open_pauses = before.filtered(lambda t: not t.date_end and t.loss_type != 'productive')
        if self.action == 'start':
            open_pauses._close()
            workorder.button_start()
        elif self.action == 'pause':
            if not self.loss_id:
                raise UserError(self.env._("Choose the reason of the pause."))
            workorder.button_pending()
            self.env['mrp.workcenter.productivity'].create({
                'workorder_id': workorder.id, 'workcenter_id': workorder.workcenter_id.id,
                'loss_id': self.loss_id.id, 'description': self.note or self.loss_id.name,
                'date_start': fields.Datetime.now()})
        elif self.action == 'quality':
            if not self.photo:
                raise UserError(self.env._("Take a photo of the check."))
            self.env['td.mebli.quality.check'].create({
                'workorder_id': workorder.id, 'name': workorder.td_quality_point or self.env._("Check"),
                'result': self.result, 'photo': self.photo, 'note': self.note, 'employee_id': self.employee_id.id})
        elif self.action == 'done':
            if workorder.td_quality_point and workorder.td_quality_state != 'pass':
                raise UserError(self.env._("First the quality step: «%s», with a photo.", workorder.td_quality_point))
            open_pauses._close()
            workorder.button_finish()
        (workorder.time_ids - before).write({'td_employee_id': self.employee_id.id})
        return {'type': 'ir.actions.act_window_close'}
