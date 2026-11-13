import hmac
from datetime import timedelta

from odoo import fields, models
from odoo.exceptions import UserError

# AC-071: 5 wrong PINs in a row lock the worker for 15 minutes. The counter is kept on the employee and written in its
# own transaction (the transaction of the failed attempt is rolled back by the error), so it survives a restart and is
# shared by all the server workers (AI-A08-12, R-11). No sleep in the worker (A-14 security 7): the lock limits guessing.
# The PIN typed on the tablet is not kept: it is erased from the wizard line in the same own transaction (A-14 security 1).
PIN_MAX_FAILURES = 5
PIN_LOCK_MINUTES = 15


class TdMebliKiosk(models.TransientModel):
    _name = 'td.mebli.kiosk'
    _description = 'Shop Floor Tablet: PIN of the Worker'

    workorder_id = fields.Many2one('mrp.workorder', string='Work Order', required=True)
    action = fields.Selection([('start', 'Taken'), ('pause', 'Pause'), ('done', 'Done'), ('quality', 'Quality Step'),
                               ('scrap', 'Scrap')],
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
    # AC-073: scrap at the workplace — the part and the reason; a repeat part is made by a new manufacturing order
    production_id = fields.Many2one(related='workorder_id.production_id')
    scrap_part_id = fields.Many2one('td.mebli.part', string='Scrapped Part',
                                    domain="[('bom_id', '=', parent_bom_id)]")
    parent_bom_id = fields.Many2one(related='workorder_id.production_id.bom_id', string='Specification')
    scrap_reason = fields.Char(string='Scrap Reason')

    def _td_pin_attempt_end(self, failed_employee=None):
        """Erase the typed PIN from the wizard line and, for a wrong PIN, +1 failure of the worker — in a transaction of
        its own, so both are committed even though a failed attempt rolls the request back."""
        lock_until = fields.Datetime.now() + timedelta(minutes=PIN_LOCK_MINUTES)
        with self.env.registry.cursor() as cr:
            cr.execute("UPDATE td_mebli_kiosk SET pin = NULL WHERE id IN %s", [tuple(self.ids) or (0,)])
            erased = cr.rowcount
            if failed_employee:
                cr.execute("""
                    UPDATE hr_employee
                       SET td_pin_fail_count = CASE WHEN COALESCE(td_pin_fail_count, 0) + 1 >= %(max)s THEN 0
                                                    ELSE COALESCE(td_pin_fail_count, 0) + 1 END,
                           td_pin_locked_until = CASE WHEN COALESCE(td_pin_fail_count, 0) + 1 >= %(max)s THEN %(until)s
                                                      ELSE td_pin_locked_until END
                     WHERE id = %(id)s
                """, {'max': PIN_MAX_FAILURES, 'until': lock_until, 'id': failed_employee.id})
        if failed_employee:
            failed_employee.invalidate_recordset(['td_pin_fail_count', 'td_pin_locked_until'])
        if not erased and self.ids:
            # the line is not committed yet (created in this same transaction by a script): erase it here
            self.env.cr.execute("UPDATE td_mebli_kiosk SET pin = NULL WHERE id IN %s", [tuple(self.ids)])
        self.invalidate_recordset(['pin'])

    def _check_pin(self):
        # sudo: the PIN is an HR field; the tablet user only compares it and never reads it back
        employee = self.employee_id.sudo()
        typed = self.pin or ''
        locked = employee.td_pin_locked_until
        if locked and locked > fields.Datetime.now():
            self._td_pin_attempt_end()
            raise UserError(self.env._("The worker is locked until %s",
                                       fields.Datetime.context_timestamp(self, locked).strftime('%H:%M')))
        # one message for every failure: the tablet does not tell whether the worker has a PIN at all
        # constant-time comparison: the time of the answer does not tell how many digits are right
        if employee.user_id or not employee.pin or not hmac.compare_digest(typed.encode(), employee.pin.encode()):
            self._td_pin_attempt_end(failed_employee=employee)
            raise UserError(self.env._("Wrong PIN"))
        self._td_pin_attempt_end()
        if employee.td_pin_fail_count or locked:
            employee.write({'td_pin_fail_count': 0, 'td_pin_locked_until': False})

    def _check_timers(self, open_work):
        """One worker at a time on a work order of the tablet. In Community the timer of a work order belongs to the
        Odoo user (the shared tablet), so a second worker would continue the timer of the first one and his time would
        be lost; «Pause» of one worker would stop the other one. The tablet refuses instead of losing the time."""
        _ = self.env._
        employee, workorder = self.employee_id, self.workorder_id
        # a timer without a worker (started outside the tablet, e.g. by the planner) is not «another worker»
        others = open_work.filtered(lambda t: t.td_employee_id and t.td_employee_id != employee)
        if others:
            who = others[0].td_employee_id.name or others[0].user_id.name
            # AC-072, SPEC text
            raise UserError(_("The work order is already done by %(who)s. Two workers on one work order from one tablet "
                              "— pause it or choose another work order.", who=who))
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
            # sudo: the tablet user may not create checks; the check is created only after the PIN of the worker
            self.env['td.mebli.quality.check'].sudo().create({
                'workorder_id': workorder.id, 'name': workorder.td_quality_point or self.env._("Check"),
                'result': self.result, 'photo': self.photo, 'note': self.note, 'employee_id': self.employee_id.id})
        elif self.action == 'scrap':
            self._td_scrap()
        elif self.action == 'done':
            if workorder.td_quality_point and workorder.td_quality_state != 'pass':
                # AC-075, SPEC text
                raise UserError(self.env._("Pass the quality step: %s", workorder.td_quality_point))
            open_pauses._close()
            workorder.button_finish()
        # the worker confirmed with the PIN: the tablet (sudo) writes him on the new time lines
        # sudo: td_employee_id of a time line is protected from users; the tablet writes the worker confirmed by the PIN
        (workorder.time_ids - before).sudo().write({'td_employee_id': self.employee_id.id})
        return {'type': 'ir.actions.act_window_close'}

    def _td_scrap(self):
        """AC-073: «Scrap» on the tablet — a manufacturing order for the repeat part (origin: the work order, the
        reason) and a line of the journal of non-conformities (td.mebli.quality.check, kind «scrap»: the dashboard)."""
        if not self.env.user.has_group('td_mebli_base.group_feature_kiosk'):
            raise UserError(self.env._("Scrap at the workplace is a function of the workshop kiosk (box B)."))
        if not self.scrap_part_id or self.scrap_part_id.bom_id != self.workorder_id.production_id.bom_id:
            raise UserError(self.env._("Choose the scrapped part of this manufacturing order."))
        if not (self.scrap_reason or '').strip():
            raise UserError(self.env._("Enter the reason of the scrap."))
        workorder = self.workorder_id
        origin = f"{workorder.production_id.name} / {workorder.name}"
        production = self.scrap_part_id._td_make_production(
            self.scrap_part_id.qty, origin, self.env._("Scrap: %s", self.scrap_reason))
        # sudo: the tablet user may not create checks; the scrap line is created only after the PIN of the worker
        check = self.env['td.mebli.quality.check'].sudo().create({
            'workorder_id': workorder.id, 'kind': 'scrap', 'result': 'fail',
            'name': self.env._("Scrap: %s", self.scrap_part_id.name), 'note': self.scrap_reason,
            'part_id': self.scrap_part_id.id, 'repeat_production_id': production.id,
            'employee_id': self.employee_id.id})
        # sudo: the tablet user only reads the manufacturing order; the scrap note is posted on its behalf
        workorder.production_id.sudo().message_post(body=self.env._(
            "Scrap of %(part)s by %(who)s: %(reason)s. Repeat part: %(production)s.",
            part=self.scrap_part_id.name, who=self.employee_id.name, reason=self.scrap_reason,
            production=production.name))
        return check
