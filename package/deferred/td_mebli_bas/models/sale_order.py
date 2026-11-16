from odoo import api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # replaces the imitation of the slice in td_mebli_ua (R-06): the status comes from the posted invoices of the order
    td_bas_state = fields.Selection([('none', 'Not Sent'), ('sent', 'Sent to BAS'), ('error', 'Exchange Error')],
                                    string='Exchange with BAS', compute='_compute_td_bas_state')

    @api.depends('invoice_ids.state', 'invoice_ids.td_bas_state')
    def _compute_td_bas_state(self):
        for order in self:
            invoices = order.invoice_ids.filtered(lambda m: m.state == 'posted')
            if any(m.td_bas_state == 'error' for m in invoices):
                order.td_bas_state = 'error'
            elif invoices and all(m.td_bas_state == 'sent' for m in invoices):
                order.td_bas_state = 'sent'
            else:
                order.td_bas_state = 'none'

    def action_td_send_bas(self):
        """«Send to BAS» on the order: its posted invoices go into a batch of the channel of the company."""
        self.env['td.mebli.bas.batch']._td_check_finance()
        batches = self.env['td.mebli.bas.batch']
        for order in self:
            moves = order.invoice_ids.filtered(lambda m: m.state == 'posted' and m.td_bas_state != 'sent')
            if not moves:
                raise UserError(self.env._("The order %s has no posted invoices to send to BAS.", order.name))
            channel = self.env['td.mebli.bas.channel']._td_channel_for(order.company_id).with_company(order.company_id)
            batches |= channel._td_export_moves(moves, 'sales')
        return batches
