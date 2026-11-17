from odoo import api, fields, models
from odoo.exceptions import UserError


class TdMebliPrintWizard(models.TransientModel):
    """A-17 №9: the button «Print» of the quotation / order opens the list of its printed forms (decision of the owner
    2026-11-16: one button with a list). The list is the standard one of ⚙ › Print: the reports bound to the sale order
    that the user may run (ir.actions.report, groups of the report)."""
    _name = 'td.mebli.print.wizard'
    _description = 'Print the Order'

    order_ids = fields.Many2many('sale.order', string='Orders', required=True)
    report_ids = fields.Many2many('ir.actions.report', string='Available Forms', compute='_compute_report_ids')
    report_id = fields.Many2one('ir.actions.report', string='Form', domain="[('id', 'in', report_ids)]")

    @api.model
    def _td_reports(self):
        # sudo: read only — the list of the bound reports (ir.actions.report is readable by the users through the
        # bindings only); the groups of every report are checked below, as the standard menu ⚙ › Print does
        reports = self.env['ir.actions.report'].sudo().search(
            [('binding_model_id.model', '=', 'sale.order'), ('binding_type', '=', 'report')], order='id')
        return reports.filtered(lambda r: not r.group_ids or (r.group_ids & self.env.user.all_group_ids))

    @api.depends('order_ids')
    def _compute_report_ids(self):
        reports = self._td_reports()
        for wizard in self:
            wizard.report_ids = reports

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if 'report_id' in fields_list and not values.get('report_id'):
            values['report_id'] = self._td_reports()[:1].id
        return values

    def action_print(self):
        self.ensure_one()
        if not self.report_id or self.report_id not in self._td_reports():
            raise UserError(self.env._("Choose a form to print."))
        action = self.report_id.report_action(self.order_ids)
        action['close_on_report_download'] = True
        return action
