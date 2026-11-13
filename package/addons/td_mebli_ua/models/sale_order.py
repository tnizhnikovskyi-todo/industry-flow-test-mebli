from odoo import api, fields, models
from odoo.exceptions import AccessError
from odoo.tools import float_compare, format_amount


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def td_action_update_prices_by_rate(self):
        """«Update Prices at the Rate» (AC-037): only quotations (state «Quotation» / «Quotation Sent») are recomputed with
        the standard price update at today's rate; confirmed orders are not changed. The chatter of each changed quotation
        gets the old and the new total."""
        if not self.env.user.has_group('td_mebli_base.group_finance'):
            raise AccessError(self.env._("Only the finance users update the prices at the rate."))
        orders = self.search([('state', 'in', ('draft', 'sent')), ('company_id', 'in', self.env.companies.ids)])
        changed = self.browse()
        now = fields.Datetime.now()
        for order in orders:
            old_total = order.amount_total
            # the standard update converts the currencies at the date of the order: the quotation gets today's rate
            order.date_order = now
            order._recompute_prices()
            if float_compare(old_total, order.amount_total, precision_rounding=order.currency_id.rounding):
                order.message_post(body=self.env._(
                    "Prices updated at the NBU rate: total %(old)s → %(new)s.",
                    old=format_amount(self.env, old_total, order.currency_id),
                    new=format_amount(self.env, order.amount_total, order.currency_id)))
                changed |= order
        return {
            'type': 'ir.actions.client', 'tag': 'display_notification',
            'params': {'type': 'success' if changed else 'info', 'sticky': False,
                       'message': self.env._("Quotations with new prices: %(count)s of %(total)s.",
                                             count=len(changed), total=len(orders))},
        }
