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
    td_over_history = fields.Boolean(string='Above History', compute='_compute_td_over_history', store=True)
    # AC-085 / AC-086: the mark of the line — «Above history +8 %», or the hint «no history» (not an error)
    td_history_note = fields.Char(string='History', compute='_compute_td_history_note')

    @api.depends('td_history_price', 'td_over_history', 'td_price_delta_pct')
    def _compute_td_history_note(self):
        for line in self:
            if not line.product_id or line.display_type:
                line.td_history_note = False
            elif not line.td_history_price:
                line.td_history_note = self.env._("no history")
            elif line.td_over_history:
                line.td_history_note = self.env._("Above history +%s %%", round(line.td_price_delta_pct))
            else:
                line.td_history_note = False

    @api.depends('price_unit', 'product_id', 'product_qty', 'product_uom_id', 'order_id.currency_id',
                 'order_id.date_order', 'order_id.state')
    def _compute_td_history_price(self):
        """AC-085: the average unit price of the earlier confirmed purchases of the product, weighted by the quantity.
        Review A-14 M3: the earlier lines may be in another currency (EUR fittings, AC-037) and in another unit — each
        price is converted into the currency of the company at the date of its order and into the unit of the product
        (`uom._compute_price`) before the average; the average is shown in the currency and the unit of this line."""
        for line in self:
            history = 0.0
            if line.product_id and line.order_id.date_order:
                start = line.order_id.date_order - timedelta(days=HISTORY_DAYS)
                earlier = self.search([
                    ('product_id', '=', line.product_id.id), ('company_id', '=', line.company_id.id),
                    ('state', 'in', ('purchase', 'done')), ('order_id.date_order', '<', line.order_id.date_order),
                    ('order_id.date_order', '>=', start), ('id', '!=', line._origin.id or 0)])
                history = line._td_average_price(earlier)
            line.td_history_price = history
            line.td_price_delta_pct = (line.price_unit - history) / history * 100.0 if history else 0.0
            line.td_overpay = (line.price_unit - history) * line.product_qty if history and line.price_unit > history else 0.0

    def _td_average_price(self, earlier):
        """Weighted average of the unit prices of `earlier` in the currency of the company and the unit of the product,
        returned in the currency (at the date of the order) and the unit of this line; 0 without history."""
        self.ensure_one()
        company = self.company_id or self.env.company
        product_uom = self.product_id.uom_id
        total = qty = 0.0
        for ln in earlier:
            line_uom = ln.product_uom_id or product_uom
            ln_qty = line_uom._compute_quantity(ln.product_qty, product_uom, round=False)
            price = ln.currency_id._convert(ln.price_unit, company.currency_id, company,
                                            ln.order_id.date_order or fields.Date.today(), round=False)
            total += line_uom._compute_price(price, product_uom) * ln_qty
            qty += ln_qty
        if not qty:
            return 0.0
        average = total / qty
        currency = self.currency_id or company.currency_id
        average = company.currency_id._convert(average, currency, company, self.order_id.date_order or fields.Date.today(),
                                               round=False)
        return product_uom._compute_price(average, self.product_uom_id or product_uom)

    @api.depends('td_history_price', 'td_price_delta_pct', 'company_id.td_price_threshold_pct')
    def _compute_td_over_history(self):
        """VP-11 (review A-14 m1): the mark follows the threshold of the company — a new threshold re-marks the stored
        lines without recomputing their history."""
        for line in self:
            line.td_over_history = bool(line.td_history_price) and \
                line.td_price_delta_pct > line.company_id.td_price_threshold_pct
