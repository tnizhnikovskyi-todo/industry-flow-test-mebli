from datetime import timedelta

from odoo import api, fields, models

# when the order has no manufacturing order yet, the workshop is assumed to need this many days (A-11: from the BoM lead time)
DEFAULT_SHOP_DAYS = 14


class TdMebliOrderItem(models.Model):
    """A made-to-order item of a furniture order (NG-01): painted fronts, a stone worktop, glass, a sliding-door profile.

    It is bought from a supplier for this order only; its supplier date moves the forecast date of the order.
    A-11: link to the purchase order line of the standard purchase flow (purchase_stock, route «Replenish on Order»)."""
    _name = 'td.mebli.order.item'
    _description = 'Made-to-order item'
    _order = 'order_id, sequence, id'

    order_id = fields.Many2one('sale.order', string='Order', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='order_id.company_id', store=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Item', required=True)
    supplier_id = fields.Many2one('res.partner', string='Supplier')
    date_supplier = fields.Date(string='Supplier Date', help="Date when the supplier delivers the item to the factory.")
    lead_days = fields.Integer(string='Days to Fit', default=2,
                               help="Days from the receipt of the item to the order being ready (fitting, packing).")
    date_ready = fields.Date(string='Ready by Item', compute='_compute_date_ready', store=True)
    state = fields.Selection(
        [('to_order', 'To Order'), ('ordered', 'Ordered'), ('confirmed', 'Confirmed by Supplier'), ('received', 'Received')],
        string='Status', default='to_order', required=True)
    is_late = fields.Boolean(string='Moves the Date', compute='_compute_is_late')

    _lead_days_positive = models.Constraint('CHECK(lead_days >= 0)', 'The days to fit cannot be negative.')

    @api.depends('date_supplier', 'lead_days', 'state')
    def _compute_date_ready(self):
        for item in self:
            if item.state == 'received' or not item.date_supplier:
                item.date_ready = False
            else:
                item.date_ready = item.date_supplier + timedelta(days=item.lead_days)

    @api.depends('date_ready', 'order_id.commitment_date')
    def _compute_is_late(self):
        for item in self:
            promised = item.order_id.commitment_date
            item.is_late = bool(item.date_ready and promised
                                and item.date_ready > fields.Date.context_today(item, promised))


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    td_item_ids = fields.One2many('td.mebli.order.item', 'order_id', string='Made-to-order Items', copy=True)
    td_shop_date = fields.Date(string='Ready by Workshop', compute='_compute_td_forecast')
    td_forecast_date = fields.Date(string='Forecast Date', compute='_compute_td_forecast',
                                   help="The later of the two: the workshop is ready, the last made-to-order item is fitted.")
    td_delay_days = fields.Integer(string='Shift, days', compute='_compute_td_forecast')
    td_late_item_id = fields.Many2one('td.mebli.order.item', string='Item that Moves the Date', compute='_compute_td_forecast')
    td_delay_reason = fields.Selection(
        [('supplier', 'Supplier'), ('company', 'Company'), ('customer', 'Customer')],
        string='Shift Reason', compute='_compute_td_delay_reason', store=True, readonly=False,
        help="Who moved the date: suggested from the forecast, the manager may set «Customer» for a change asked by the customer.")

    def _td_shop_date(self):
        """The date the workshop finishes the order: the planned end of its manufacturing orders, else the BoM lead time."""
        self.ensure_one()
        # sudo: the salesperson sees the dates of the manufacturing orders of his order, not the orders themselves
        productions = self.sudo().mrp_production_ids.filtered(lambda p: p.state != 'cancel')
        ends = [p.date_finished for p in productions if p.date_finished]
        if ends:
            return fields.Date.context_today(self, max(ends))
        days = max([line.td_bom_id.produce_delay for line in self.order_line if line.td_bom_id] or [DEFAULT_SHOP_DAYS])
        start = fields.Date.context_today(self, self.date_order) if self.date_order else fields.Date.context_today(self)
        return start + timedelta(days=days or DEFAULT_SHOP_DAYS)

    @api.depends('td_item_ids.date_ready', 'commitment_date', 'date_order', 'state')
    def _compute_td_forecast(self):
        for order in self:
            if order.state == 'cancel':
                order.td_shop_date = order.td_forecast_date = order.td_late_item_id = False
                order.td_delay_days = 0
                continue
            shop = order._td_shop_date()
            items = order.td_item_ids.filtered('date_ready').sorted('date_ready')
            last = items[-1:]
            forecast = max(shop, last.date_ready) if last else shop
            order.td_shop_date = shop
            order.td_forecast_date = forecast
            order.td_late_item_id = last if last and last.date_ready >= shop else False
            if order.commitment_date:
                promised = fields.Date.context_today(order, order.commitment_date)
                order.td_delay_days = max((forecast - promised).days, 0)
            else:
                order.td_delay_days = 0

    @api.depends('td_item_ids.date_ready', 'commitment_date')
    def _compute_td_delay_reason(self):
        for order in self:
            if order.td_delay_reason == 'customer':
                continue  # set by the manager: a change asked by the customer stays the reason
            if not order.td_delay_days:
                order.td_delay_reason = False
            else:
                order.td_delay_reason = 'supplier' if order.td_late_item_id else 'company'
