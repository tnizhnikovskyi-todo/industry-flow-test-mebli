from collections import defaultdict
from datetime import timedelta

import pytz

from odoo import api, fields, models
from odoo.fields import Domain

FORECAST_BATCH = 200  # orders per batch of the daily forecast cron (review A-11)
FORECAST_CURSOR = 'td_mebli_sale.forecast_cursor'  # id of the last order of the forecast cron
FORECAST_FIELDS = ('td_shop_date', 'td_forecast_date', 'td_delay_days', 'td_late_item', 'td_delay_reason')

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

    # AC-083: delayed deliveries — the date the item is needed against the date of the supplier
    td_need_date = fields.Date(string='Needed by', compute='_compute_td_late',
                               help="Read only: when the manufacturing order that consumes the item plans to start (the "
                                    "date of its component move), else the promised date of the sales order.")
    td_late_days = fields.Integer(string='Late, days', compute='_compute_td_late',
                                  help="Read only: the expected arrival (supplier date + the average delay of the supplier) "
                                       "minus the date the item is needed.")
    td_is_late = fields.Boolean(string='Delayed', compute='_compute_td_late', search='_search_td_is_late')
    td_sale_order_ids = fields.Many2many('sale.order', string='Customer Orders', compute='_compute_td_late',
                                         help="The sales orders this purchased item is for (standard links of the purchase).")

    def _td_need_date(self):
        self.ensure_one()
        # sudo: read only — the stock moves of the manufacturing orders
        dests = self.env['stock.move'].sudo().browse(self.sudo().move_dest_ids._rollup_move_dests())
        dates = [move.date for move in dests if move.date and move.state not in ('done', 'cancel')]
        if dates:
            return fields.Date.context_today(self, min(dates))
        orders = self._td_sale_orders().filtered('commitment_date')
        dates = [order.commitment_date for order in orders]
        return fields.Date.context_today(self, min(dates)) if dates else False

    def _compute_td_late(self):
        for line in self:
            need = line._td_need_date() if line.id and line._td_is_open() else False
            line.td_need_date = need
            arrival = (fields.Date.context_today(line, line.date_planned) + timedelta(days=line.td_supplier_delay)
                       if need and line.date_planned else False)
            line.td_late_days = max((arrival - need).days, 0) if arrival else 0
            line.td_is_late = line.td_late_days > 0
            line.td_sale_order_ids = line._td_sale_orders().sudo(False) if line.id else False

    def _search_td_is_late(self, operator, value):
        if operator != 'in':
            return NotImplemented
        open_lines = self.search([('state', '=', 'purchase'), ('display_type', '=', False)]).filtered(
            lambda line: line.qty_received < line.product_qty)
        late = open_lines.filtered('td_is_late')
        domain = Domain('id', 'in', late.ids)
        if True in value and False in value:
            return Domain.TRUE
        return domain if True in value else ~domain

    def action_td_open_sale_orders(self):
        self.ensure_one()
        orders = self.td_sale_order_ids
        action = {'type': 'ir.actions.act_window', 'res_model': 'sale.order'}
        if len(orders) == 1:
            return dict(action, view_mode='form', views=[(False, 'form')], res_id=orders.id)
        return dict(action, name=self.env._("Customer Orders"), view_mode='list,form', views=[(False, 'list'), (False, 'form')],
                    domain=[('id', 'in', orders.ids)])

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


    def _td_sale_orders(self):
        """The sales orders whose forecast this purchase line moves (read only)."""
        orders = self.env['sale.order']
        for line in self.sudo():
            orders |= line._td_productions().reference_ids.sale_ids | line.sale_line_id.order_id
        return orders

    def write(self, vals):
        result = super().write(vals)
        if {'date_planned', 'product_qty', 'qty_received'} & set(vals):
            self._td_sale_orders()._td_recompute_forecast()
        return result


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def write(self, vals):
        result = super().write(vals)
        if 'state' in vals or 'date_planned' in vals:
            self.order_line._td_sale_orders()._td_recompute_forecast()
        return result


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
    # stored (the board groups by the reason, AC-066): recomputed by the stored dependencies below, by the writes of the
    # purchase lines and orders (their dates are not stored dependencies) and by the daily scheduled action
    td_shop_date = fields.Date(string='Ready by Workshop', compute='_compute_td_forecast', store=True)
    td_forecast_date = fields.Date(string='Forecast Date', compute='_compute_td_forecast', store=True,
                                   help="The later of the two: the workshop is ready, the last purchased item arrives and is "
                                        "made into the product (manufacturing lead time of the bill of materials).")
    td_delay_days = fields.Integer(string='Shift, days', compute='_compute_td_forecast', store=True)
    td_late_line_id = fields.Many2one('purchase.order.line', string='Purchase that Moves the Date',
                                      compute='_compute_td_purchase_lines',
                                      groups='sales_team.group_sale_salesman,purchase.group_purchase_user')
    td_late_item = fields.Char(string='Item that Moves the Date', compute='_compute_td_forecast', store=True)
    td_delay_reason = fields.Selection(
        [('customer', 'Customer'), ('company', 'Company'), ('supplier', 'Supplier'),
         ('distributor', 'Cutting at the Distributor')],
        string='Shift Reason', compute='_compute_td_forecast', store=True,
        help="Read only (AC-066): «Customer» when the last fixed change of the order was asked by the customer, "
             "«Cutting at the Distributor» when the parts cut by the distributor come back last, «Supplier» when a "
             "purchased item arrives too late for the promised date, «Company» when the workshop is late.")

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

    def _td_company_date(self, value):
        """The date of a UTC datetime in the time zone of the company of the order (its working calendar, then its
        partner; Europe/Kyiv by default) — not in the time zone of the user who happens to compute."""
        self.ensure_one()
        company = self.company_id or self.env.company
        tz = pytz.timezone(company.resource_calendar_id.tz or company.partner_id.tz or 'Europe/Kyiv')
        return pytz.utc.localize(fields.Datetime.to_datetime(value)).astimezone(tz).date()

    def _td_distributor_date(self):
        """The date the parts cut by the distributor come back (VP-09). No cutting job here: td_mebli_cutting overrides
        it (A-11 G2 tail). False = no cutting at the distributor."""
        self.ensure_one()
        return False

    def _td_recompute_forecast(self):
        """Recompute the stored forecast now: the purchase dates and the receipts are not stored dependencies."""
        orders = self.filtered(lambda o: isinstance(o.id, int))
        if not orders:
            return
        for fname in FORECAST_FIELDS:
            self.env.add_to_compute(self._fields[fname], orders)
        orders._recompute_recordset(FORECAST_FIELDS)

    @api.model
    def _td_forecast_open_domain(self):
        """Orders whose forecast still matters (review A-11): confirmed and not delivered in full. td_mebli_install
        adds «without a signed final act»."""
        return [('state', '=', 'sale'), ('delivery_status', '!=', 'full')]

    @api.model
    def _cron_td_recompute_forecast(self, batch_size=FORECAST_BATCH):
        """Daily: the forecast of the open orders only, in batches. The id of the last recomputed order is kept in
        `td_mebli_sale.forecast_cursor` (review A-11, round 2): a run stopped by the time limit of the cron continues
        after it next time instead of starting from the beginning; after a full pass the cursor is reset to 0. Each
        batch is committed with `ir.cron._commit_progress` (done / remaining)."""
        Param = self.env['ir.config_parameter'].sudo()
        try:
            cursor = int(Param.get_param(FORECAST_CURSOR) or 0)
        except ValueError:
            cursor = 0
        orders = self.search(self._td_forecast_open_domain() + [('id', '>', cursor)], order='id')
        in_cron = bool(self.env.context.get('ir_cron_progress_id'))
        Cron = self.env['ir.cron']
        if in_cron:
            Cron._commit_progress(remaining=len(orders))
        for start in range(0, len(orders), batch_size):
            batch = orders[start:start + batch_size]
            batch._td_recompute_forecast()
            Param.set_param(FORECAST_CURSOR, str(batch[-1].id))
            if in_cron and not Cron._commit_progress(len(batch), remaining=len(orders) - start - len(batch)):
                return  # the time of the run is over: the next run continues after the cursor
        Param.set_param(FORECAST_CURSOR, '0')  # the full pass is done: the next day starts from the beginning

    @api.depends('state', 'commitment_date', 'date_order', 'order_line.td_bom_id.produce_delay',
                 'stock_reference_ids.production_ids.date_finished', 'stock_reference_ids.production_ids.state',
                 'td_change_ids.state', 'td_change_ids.reason')
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
            distributor = order._td_distributor_date()
            if distributor and distributor > forecast:
                forecast, late = distributor, lines.browse()
            order.td_shop_date = shop
            order.td_forecast_date = forecast
            order.td_late_item = f'{late.product_id.name} — {late.partner_id.name}' if late else False
            if order.commitment_date:
                # review A-11: the promised day in the time zone of the company (the cron has no user time zone)
                promised = order._td_company_date(order.commitment_date)
                order.td_delay_days = max((forecast - promised).days, 0)
            else:
                order.td_delay_days = 0
            changes = order.td_change_ids.filtered(lambda c: c.state != 'open').sorted('version')
            if not order.td_delay_days:
                order.td_delay_reason = False
            elif changes[-1:].reason == 'customer':
                order.td_delay_reason = 'customer'
            elif distributor and forecast == distributor and not late:
                order.td_delay_reason = 'distributor'
            else:
                order.td_delay_reason = 'supplier' if late else 'company'
