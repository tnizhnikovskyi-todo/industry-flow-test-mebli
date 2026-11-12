from collections import defaultdict
from datetime import timedelta

from odoo import fields, models

# when the order has no manufacturing order yet, the workshop is assumed to need this many days
# (only for a quotation whose order BoM has no manufacturing lead time, produce_delay = 0)
DEFAULT_SHOP_DAYS = 14


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    td_date_ready = fields.Date(
        string='Order Ready by Item', compute='_compute_td_date_ready',
        help="Read only. The expected delivery date of the line (Purchase), plus the average delay of this supplier in "
             "the history of receipts, plus the manufacturing lead time of the bill of materials that consumes it: when "
             "the sales order can be ready if only this item is waited for. Empty when the item is received or the "
             "purchase is cancelled.")
    td_supplier_delay = fields.Integer(
        string='Supplier Delay by History, days', compute='_compute_td_date_ready',
        help="Read only: the average delay of the supplier over the past year (received purchase lines: the receipt "
             "date against the expected arrival), rounded to days; early deliveries count as on time.")

    def _td_productions(self):
        """The manufacturing orders that consume the purchased item (standard MTO chain: the purchase line feeds the
        component move of the manufacturing order). With a receipt in 2 or 3 steps the line feeds the input move, so the
        chain of destination moves is followed (standard _rollup_move_dests, as purchase_mrp does in the MO overview).
        Read only: sudo reads the stock moves, which a salesperson may not read; nothing is written."""
        self.ensure_one()
        Move = self.env['stock.move'].sudo()
        moves = Move.browse(self.sudo().move_dest_ids._rollup_move_dests())
        return moves.raw_material_production_id

    def _td_production(self):
        self.ensure_one()
        return self._td_productions()[:1]

    def _td_is_open(self):
        self.ensure_one()
        return (not self.display_type and self.state != 'cancel'
                and self.qty_received < self.product_qty and bool(self.date_planned))

    def _compute_td_date_ready(self):
        delays = self.partner_id._td_supplier_delays()
        for line in self:
            line.td_supplier_delay = int(delays.get(line.partner_id.id, (0.0, 0))[0] + 0.5)
            if not line._td_is_open():
                line.td_date_ready = False
                continue
            arrival = fields.Date.context_today(line, line.date_planned) + timedelta(days=line.td_supplier_delay)
            # sudo: the bill of materials of the manufacturing order is read only (produce_delay)
            line.td_date_ready = arrival + timedelta(days=line._td_production().sudo().bom_id.produce_delay or 0)


class ResPartner(models.Model):
    """Position 29: reliability of a supplier from the history of purchases (read only, nothing is entered).

    The standard keeps the on-time rate of a vendor (purchase_stock: res.partner.on_time_rate, the share of the ordered
    quantity received by the expected arrival); the forecast date needs days, so the same history (received purchase lines
    of the past year, the receipt date of the done stock move against the expected arrival of the line) gives the average
    delay in days."""
    _inherit = 'res.partner'

    td_supplier_delay_avg = fields.Float(
        string='Average Delay, days', compute='_compute_td_supplier_delay', digits=(16, 1),
        groups='purchase.group_purchase_user,sales_team.group_sale_salesman',
        help="Read only: received purchase lines of the past year, the receipt date against the expected arrival; "
             "early deliveries count as on time. Added to the supplier date in the forecast date of the order.")
    td_supplier_delay_lines = fields.Integer(
        string='Receipts in the Statistics', compute='_compute_td_supplier_delay',
        groups='purchase.group_purchase_user,sales_team.group_sale_salesman')

    def _td_supplier_delays(self):
        """{partner id: (average delay in days, number of received purchase lines)} over the past year."""
        partners = self.filtered('id')
        if not partners:
            return {}
        days = int(self.env['ir.config_parameter'].sudo().get_param('purchase_stock.on_time_delivery_days', default='365'))
        # sudo: read only — the forecast date of a sales order is computed for a salesperson too
        moves = self.env['stock.move'].sudo().search_fetch([
            ('purchase_line_id.partner_id', 'in', partners.ids),
            ('purchase_line_id.date_order', '>', fields.Date.today() - timedelta(days=days)),
            ('state', '=', 'done'), ('location_dest_id.usage', '=', 'internal'),
        ], ['purchase_line_id', 'date'])
        last = {}
        for move in moves:  # the last receipt of a line closes it
            line = move.purchase_line_id
            if line.date_planned and (line.id not in last or move.date > last[line.id][1]):
                last[line.id] = (line, move.date)
        stats = defaultdict(list)
        for line, done in last.values():
            stats[line.partner_id.id].append(max(0, (done.date() - line.date_planned.date()).days))
        return {pid: (sum(values) / len(values), len(values)) for pid, values in stats.items()}

    def _compute_td_supplier_delay(self):
        delays = self._td_supplier_delays()
        for partner in self:
            partner.td_supplier_delay_avg, partner.td_supplier_delay_lines = delays.get(partner.id, (0.0, 0))


class SaleOrder(models.Model):
    """S-02: the forecast date of the order is read from the standard documents only.

    The workshop: the planned end of the manufacturing orders of the order (Manufacturing). The made-to-order items
    (painted fronts, a stone worktop, a sliding-door profile): products with the routes «Replenish on Order (MTO)» and
    «Buy», the supplier in the vendor pricelist; the confirmation of the sales order creates the purchase orders and the
    supplier date is the expected arrival of the purchase line (Purchase). Nothing is entered here: td_ reads and adds up."""
    _inherit = 'sale.order'

    td_purchase_line_ids = fields.Many2many(
        'purchase.order.line', string='Purchased for the Order', compute='_compute_td_purchase_lines',
        groups='sales_team.group_sale_salesman,purchase.group_purchase_user')
    td_shop_date = fields.Date(string='Ready by Workshop', compute='_compute_td_forecast')
    td_forecast_date = fields.Date(string='Forecast Date', compute='_compute_td_forecast',
                                   help="The later of the two: the workshop is ready, the last purchased item arrives and is "
                                        "made into the product (manufacturing lead time of the bill of materials).")
    td_delay_days = fields.Integer(string='Shift, days', compute='_compute_td_forecast')
    td_late_line_id = fields.Many2one('purchase.order.line', string='Purchase that Moves the Date',
                                      compute='_compute_td_purchase_lines',
                                      groups='sales_team.group_sale_salesman,purchase.group_purchase_user')
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
        sale_purchase_stock: _get_purchase_orders), only those bought for this order: the line feeds a manufacturing
        order of this order (a request for quotation may be merged with the purchases of other orders,
        purchase_stock _merge_po_post_process) or is bought for one of its lines (sale_purchase services)."""
        self.ensure_one()
        # sudo: read only — the forecast date and the reason are computed for a salesperson too; the lines are given to
        # the views without sudo (the access rule «purchases of my orders» decides what he reads)
        order = self.sudo()
        productions = order.mrp_production_ids
        return order._get_purchase_orders().order_line.filtered(
            lambda line: not line.display_type and line.state != 'cancel'
            and (line._td_productions() & productions or line.sale_line_id in order.order_line))

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
