import time

from odoo import fields, models
from odoo.exceptions import UserError

# wrong PIN: a short delay on every failure and a lock of the worker after several failures in a row (in the memory of
# the server process: the transaction of a failed attempt is rolled back, so a counter in the database would be lost)
PIN_DELAY_SECONDS = 1.0
PIN_MAX_FAILURES = 5
PIN_LOCK_SECONDS = 300
_PIN_FAILURES = {}  # (database, employee id) -> (failures in a row, time of the last failure)


class TdMebliKiosk(models.TransientModel):
    _name = 'td.mebli.kiosk'
    _description = 'Shop Floor Tablet: PIN of the Worker'

    workorder_id = fields.Many2one('mrp.workorder', string='Work Order', required=True)
    action = fields.Selection([('start', 'Taken'), ('pause', 'Pause'), ('done', 'Done'), ('quality', 'Quality Step')],
                              string='Action', required=True, default='start')
    # shop workers: employees without an own Odoo user, they work through the shared tablet with the PIN
    employee_id = fields.Many2one('hr.employee', string='Worker', required=True,
                                  domain="[('user_id', '=', False), ('company_id', '=', company_id)]")
    company_id = fields.Many2one(related='workorder_id.company_id')
    pin = fields.Char(string='PIN')
    loss_id = fields.Many2one('mrp.workcenter.productivity.loss', string='Pause Reason',
                              domain="[('loss_type', 'in', ('availability', 'quality', 'performance'))]")
    quality_point = fields.Char(related='workorder_id.td_quality_point')
    result = fields.Selection([('pass', 'Passed'), ('fail', 'Failed')], string='Result', default='pass')
    photo = fields.Image(string='Photo', max_width=1024, max_height=1024)
    note = fields.Char(string='Note')

    def _check_pin(self):
        employee = self.employee_id.sudo()  # the PIN is an HR field; the tablet user only compares it
        key = (self.env.cr.dbname, employee.id)
        failures, last = _PIN_FAILURES.get(key, (0, 0.0))
        if failures >= PIN_MAX_FAILURES and time.monotonic() - last < PIN_LOCK_SECONDS:
            raise UserError(self.env._("Too many wrong PINs: try again in 5 minutes or ask the shop manager."))
        # one message for every failure: the tablet does not tell whether the worker has a PIN at all
        if employee.user_id or not employee.pin or (self.pin or '') != employee.pin:
            _PIN_FAILURES[key] = (failures + 1 if failures < PIN_MAX_FAILURES else 1, time.monotonic())
            time.sleep(PIN_DELAY_SECONDS)
            raise UserError(self.env._("Wrong worker or PIN."))
        _PIN_FAILURES.pop(key, None)

    def _check_timers(self, open_work):
        """One worker at a time on a work order of the tablet. In Community the timer of a work order belongs to the
        Odoo user (the shared tablet), so a second worker would continue the timer of the first one and his time would
        be lost; «Pause» of one worker would stop the other one. The tablet refuses instead of losing the time."""
        _ = self.env._
        employee, workorder = self.employee_id, self.workorder_id
        others = open_work.filtered(lambda t: t.td_employee_id != employee)
        if others:
            who = others[0].td_employee_id.name or others[0].user_id.name
            raise UserError(_("%(who)s is working on %(wo)s now: one worker at a time. %(who)s presses «Pause» or "
                              "«Done» first.", who=who, wo=workorder.display_name))
        if self.action == 'start':
            elsewhere = self.env['mrp.workcenter.productivity'].search([
                ('td_employee_id', '=', employee.id), ('date_end', '=', False), ('loss_type', '=', 'productive'),
                ('workorder_id', '!=', workorder.id)], limit=1)
            if elsewhere:
                raise UserError(_("%(who)s is already working on %(wo)s: press «Pause» or «Done» there first.",
                                  who=employee.name, wo=elsewhere.workorder_id.display_name))
        if self.action == 'pause' and not open_work:
            raise UserError(_("%s has no running work on this work order: nothing to pause.", employee.name))

    def action_confirm(self):
        self.ensure_one()
        self._check_pin()
        workorder = self.workorder_id
        before = workorder.time_ids
        open_pauses = before.filtered(lambda t: not t.date_end and t.loss_type != 'productive')
        open_work = before.filtered(lambda t: not t.date_end and t.loss_type == 'productive')
        if self.action in ('start', 'pause', 'done'):
            self._check_timers(open_work)
        if self.action == 'start':
            if open_work:  # the worker has already taken it
                return {'type': 'ir.actions.act_window_close'}
            open_pauses._close()
            workorder.button_start()
        elif self.action == 'pause':
            if not self.loss_id:
                raise UserError(self.env._("Choose the reason of the pause."))
            open_work._close()  # only the line of this worker (checked above), not «the line of the tablet user»
            self.env['mrp.workcenter.productivity'].create({
                'workorder_id': workorder.id, 'workcenter_id': workorder.workcenter_id.id,
                'loss_id': self.loss_id.id, 'description': self.note or self.loss_id.name,
                'date_start': fields.Datetime.now()})
        elif self.action == 'quality':
            if not self.photo:
                raise UserError(self.env._("Take a photo of the check."))
            # the check is created by the tablet after the PIN: the users of manufacturing cannot create it themselves
            self.env['td.mebli.quality.check'].sudo().create({
                'workorder_id': workorder.id, 'name': workorder.td_quality_point or self.env._("Check"),
                'result': self.result, 'photo': self.photo, 'note': self.note, 'employee_id': self.employee_id.id})
        elif self.action == 'done':
            if workorder.td_quality_point and workorder.td_quality_state != 'pass':
                raise UserError(self.env._("First the quality step: «%s», with a photo.", workorder.td_quality_point))
            open_pauses._close()
            workorder.button_finish()
        # the worker confirmed with the PIN: the tablet (sudo) writes him on the new time lines
        (workorder.time_ids - before).sudo().write({'td_employee_id': self.employee_id.id})
        return {'type': 'ir.actions.act_window_close'}
