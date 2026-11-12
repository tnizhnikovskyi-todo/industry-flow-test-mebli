from datetime import timedelta

from odoo import fields, models

# when the order has no manufacturing order yet, the workshop is assumed to need this many days
# (only for a quotation whose order BoM has no manufacturing lead time, produce_delay = 0)
DEFAULT_SHOP_DAYS = 14


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    td_date_ready = fields.Date(
        string='Order Ready by Item', compute='_compute_td_date_ready',
        help="Read only. The expected delivery date of the line (Purchase) plus the manufacturing lead time of the "
             "bill of materials that consumes it: when the sales order can be ready if only this item is waited for. "
             "Empty when the item is received or the purchase is cancelled.")

    def _td_production(self):
        """The manufacturing order that consumes the purchased item (standard MTO chain: the purchase line feeds the
        component move of the manufacturing order)."""
        self.ensure_one()
        return self.move_dest_ids.raw_material_production_id[:1]

    def _td_is_open(self):
        self.ensure_one()
        return (not self.display_type and self.state != 'cancel'
                and self.qty_received < self.product_qty and bool(self.date_planned))

    def _compute_td_date_ready(self):
        for line in self:
            if not line._td_is_open():
                line.td_date_ready = False
                continue
            arrival = fields.Date.context_today(line, line.date_planned)
            line.td_date_ready = arrival + timedelta(days=line._td_production().bom_id.produce_delay or 0)


class SaleOrder(models.Model):
    """S-02: the forecast date of the order is read from the standard documents only.

    The workshop: the planned end of the manufacturing orders of the order (Manufacturing). The made-to-order items
    (painted fronts, a stone worktop, a sliding-door profile): products with the routes «Replenish on Order (MTO)» and
    «Buy», the supplier in the vendor pricelist; the confirmation of the sales order creates the purchase orders and the
    supplier date is the expected arrival of the purchase line (Purchase). Nothing is entered here: td_ reads and adds up."""
    _inherit = 'sale.order'

    td_purchase_line_ids = fields.Many2many(
        'purchase.order.line', string='Purchased for the Order', compute='_compute_td_purchase_lines',
        groups='purchase.group_purchase_user')
    td_shop_date = fields.Date(string='Ready by Workshop', compute='_compute_td_forecast')
    td_forecast_date = fields.Date(string='Forecast Date', compute='_compute_td_forecast',
                                   help="The later of the two: the workshop is ready, the last purchased item arrives and is "
                                        "made into the product (manufacturing lead time of the bill of materials).")
    td_delay_days = fields.Integer(string='Shift, days', compute='_compute_td_forecast')
    td_late_line_id = fields.Many2one('purchase.order.line', string='Purchase that Moves the Date',
                                      compute='_compute_td_purchase_lines', groups='purchase.group_purchase_user')
    td_late_item = fields.Char(string='Item that Moves the Date', compute='_compute_td_forecast')
    td_delay_reason = fields.Selection(
        [('supplier', 'Supplier'), ('company', 'Company')], string='Shift Reason', compute='_compute_td_forecast',
        help="Read only: «Supplier» when a purchased item arrives too late for the promised date, «Company» when the "
             "workshop is late.")

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

    def _td_purchase_lines(self):
        """The lines of the purchase orders linked to the sales order by the standard (sale_purchase,
        sale_purchase_stock: _get_purchase_orders)."""
        self.ensure_one()
        # sudo: a salesperson without purchase rights still gets the forecast date and the reason
        return self.sudo()._get_purchase_orders().order_line.filtered(lambda line: not line.display_type and line.state != 'cancel')

    def _td_late_line(self, lines, shop):
        """The purchased item that arrives last, if it is ready later than the workshop."""
        last = lines.filtered('td_date_ready').sorted('td_date_ready')[-1:]
        return last if last and last.td_date_ready > shop else lines.browse()

    def _compute_td_purchase_lines(self):
        """The tab and the late purchase line: for the users of Purchase only (the standard purchase rights)."""
        for order in self:
            lines = order._td_purchase_lines() if order.id else self.env['purchase.order.line'].sudo()
            order.td_purchase_line_ids = lines.sudo(False)
            late = order._td_late_line(lines, order._td_shop_date()) if order.state != 'cancel' else lines.browse()
            order.td_late_line_id = late.sudo(False)

    def _compute_td_forecast(self):
        for order in self:
            lines = order._td_purchase_lines() if order.id else self.env['purchase.order.line'].sudo()
            if order.state == 'cancel':
                order.td_shop_date = order.td_forecast_date = False
                order.td_late_item = order.td_delay_reason = False
                order.td_delay_days = 0
                continue
            shop = order._td_shop_date()
            late = order._td_late_line(lines, shop)
            forecast = late.td_date_ready if late else shop
            order.td_shop_date = shop
            order.td_forecast_date = forecast
            order.td_late_item = f'{late.product_id.name} — {late.partner_id.name}' if late else False
            if order.commitment_date:
                promised = fields.Date.context_today(order, order.commitment_date)
                order.td_delay_days = max((forecast - promised).days, 0)
            else:
                order.td_delay_days = 0
            if not order.td_delay_days:
                order.td_delay_reason = False
            else:
                order.td_delay_reason = 'supplier' if late else 'company'
