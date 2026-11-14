from odoo import api, fields, models
from odoo.exceptions import UserError

from .account_move import bas_locked_error

LOCKED_ACCRUAL = {'employee_id', 'date', 'kind', 'amount', 'hours', 'piece_rate', 'reason', 'company_id', 'state'}


class TdMebliAccrual(models.Model):
    _inherit = 'td.mebli.accrual'

    bas_state = fields.Selection([('sent', 'Sent to BAS'), ('error', 'Exchange Error')], string='Exchange with BAS',
                                 readonly=True, copy=False, index=True)
    bas_batch_id = fields.Many2one('td.mebli.bas.batch', string='BAS Batch', readonly=True, copy=False)

    def write(self, vals):
        if LOCKED_ACCRUAL & set(vals) and not self.env.su and any(a.bas_state == 'sent' for a in self):
            raise bas_locked_error(self.env)
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_sent_to_bas(self):
        """AC-041: an accrual sent to BAS is not deleted in Odoo (review A-14 L-1: a check of `ondelete`, not a raise in
        `unlink`, so the uninstallation of the module and the cascades are not blocked)."""
        if not self.env.su and any(a.bas_state == 'sent' for a in self):
            raise bas_locked_error(self.env)

    def action_td_send_bas(self):
        """«Send to BAS» (AC-109): the confirmed accruals not sent yet, one batch per company."""
        self.env['td.mebli.bas.batch']._td_check_finance()
        accruals = self.filtered(lambda a: a.state == 'confirmed' and a.bas_state != 'sent')
        if not accruals:
            raise UserError(self.env._("No confirmed accruals to send to BAS."))
        batches = self.env['td.mebli.bas.batch']
        for company in accruals.company_id:
            channel = self.env['td.mebli.bas.channel']._td_channel_for(company).with_company(company)
            batches |= channel._td_export_accruals(accruals.filtered(lambda a: a.company_id == company))
        return batches
