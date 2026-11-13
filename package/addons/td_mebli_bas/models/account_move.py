from odoo import fields, models
from odoo.exceptions import UserError

# fields of a document sent to BAS that change its sum, partner or lines (AC-041)
LOCKED_MOVE = {'partner_id', 'commercial_partner_id', 'invoice_line_ids', 'line_ids', 'amount_total', 'amount_untaxed',
               'currency_id', 'date', 'invoice_date', 'state', 'move_type', 'journal_id'}


def bas_locked_error(env):
    return UserError(env._("The document has already been sent to BAS — corrections only by a reversal."))


class AccountMove(models.Model):
    _inherit = 'account.move'

    td_bas_state = fields.Selection([('sent', 'Sent to BAS'), ('error', 'Exchange Error')], string='Exchange with BAS',
                                    readonly=True, copy=False, tracking=True, index=True)
    td_bas_batch_id = fields.Many2one('td.mebli.bas.batch', string='BAS Batch', readonly=True, copy=False)

    def _td_check_bas_lock(self):
        if not self.env.su and any(move.td_bas_state == 'sent' for move in self):
            raise bas_locked_error(self.env)

    def write(self, vals):
        if LOCKED_MOVE & set(vals):
            self._td_check_bas_lock()
        return super().write(vals)

    def button_draft(self):
        self._td_check_bas_lock()
        return super().button_draft()

    def button_cancel(self):
        self._td_check_bas_lock()
        return super().button_cancel()
