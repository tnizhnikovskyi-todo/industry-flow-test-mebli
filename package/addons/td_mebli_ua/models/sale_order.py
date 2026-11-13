from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    td_bas_state = fields.Selection(
        [('none', 'Not Sent'), ('sent', 'Sent to BAS'), ('error', 'Exchange Error')], string='Exchange with BAS',
        default='none', copy=False, readonly=True,
        help="Imitation in the slice: the status the exchange with BAS/BAF of the customer will set (H-12).")

    def action_td_send_bas(self):
        """Imitation of the exchange: marks the order as sent; the real exchange is a separate integration."""
        self.write({'td_bas_state': 'sent'})
        return True
