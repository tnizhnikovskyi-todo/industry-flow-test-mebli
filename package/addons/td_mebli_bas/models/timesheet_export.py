import base64

from odoo import api, models
from odoo.exceptions import UserError


class TdMebliTimesheetExport(models.TransientModel):
    _inherit = 'td.mebli.timesheet.export'

    @api.model
    def _td_personnel_code(self, employee):
        """The external code of BAS first; without it the Badge ID (the personnel code of the slice)."""
        # sudo: read only — the BAS code of the employee (HR data) for the user of the time sheet
        return employee.sudo().td_bas_code or super()._td_personnel_code(employee)

    def action_td_send_bas(self):
        """AC-078: the built time sheet goes into a batch «Time Sheet» of the channel of the company."""
        self.ensure_one()
        self.env['td.mebli.bas.batch']._td_check_finance()
        if not self.file:
            raise UserError(self.env._("Build the file first."))
        channel = self.env['td.mebli.bas.channel']._td_channel_for(self.env.company)
        batch = channel._td_export_timesheet(base64.b64decode(self.file), self.filename,
                                             len(self.line_ids.filtered(lambda l: not l.skipped)))
        return {'type': 'ir.actions.act_window', 'res_model': batch._name, 'res_id': batch.id, 'view_mode': 'form',
                'target': 'current'}
