from datetime import timedelta

from odoo import api, fields, models

HISTORY_DAYS = 180


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    td_history_price = fields.Monetary(
        string='Average Earlier Price', compute='_compute_td_history_price', store=True,
        help="Average unit price of the confirmed purchases of this product during the %s days before this order." % HISTORY_DAYS)
    td_price_delta_pct = fields.Float(string='Against History, %', compute='_compute_td_history_price', store=True,
                                      digits=(16, 1), aggregator='avg')
    td_overpay = fields.Monetary(string='Overpay', compute='_compute_td_history_price', store=True)
    td_over_history = fields.Boolean(string='Above History', compute='_compute_td_history_price', store=True)

    @api.depends('price_unit', 'product_id', 'product_qty', 'order_id.date_order', 'order_id.state')
    def _compute_td_history_price(self):
        for line in self:
            history = 0.0
            if line.product_id and line.order_id.date_order:
                start = line.order_id.date_order - timedelta(days=HISTORY_DAYS)
                earlier = self.search([
                    ('product_id', '=', line.product_id.id), ('company_id', '=', line.company_id.id),
                    ('state', 'in', ('purchase', 'done')), ('order_id.date_order', '<', line.order_id.date_order),
                    ('order_id.date_order', '>=', start), ('id', '!=', line._origin.id or 0)])
                qty = sum(earlier.mapped('product_qty'))
                history = sum(ln.price_unit * ln.product_qty for ln in earlier) / qty if qty else 0.0
            line.td_history_price = history
            line.td_price_delta_pct = (line.price_unit - history) / history * 100.0 if history else 0.0
            line.td_overpay = (line.price_unit - history) * line.product_qty if history and line.price_unit > history else 0.0
            line.td_over_history = bool(history) and line.td_price_delta_pct > line.company_id.td_price_threshold_pct  # VP-11
