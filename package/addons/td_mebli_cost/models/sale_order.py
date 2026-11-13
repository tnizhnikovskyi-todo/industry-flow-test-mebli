from odoo import api, fields, models

# AC-115 (security.md §4): the planned cost is seen by «Sees the margin», the finance and the sales manager;
# the actual cost and margin only by the finance (the director group implies it, td_mebli_dashboard)
PLAN_GROUPS = 'td_mebli_base.group_margin_view,td_mebli_base.group_finance,sales_team.group_sale_manager'
FACT_GROUPS = 'td_mebli_base.group_finance'


class ResCompany(models.Model):
    _inherit = 'res.company'

    td_cost_piecework = fields.Boolean(
        string='Cost: Piecework instead of Hours', default=False,
        help="Parameter of the report «Cost: plan vs actual» (AC-114): the actual work is the piecework accruals "
             "instead of the hours at the hourly cost of the work center (no double count when the hourly cost has no "
             "wages). The crew percent is always added.")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    td_cost_piecework = fields.Boolean(related='company_id.td_cost_piecework', readonly=False)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    td_cost_plan = fields.Monetary(string='Planned Cost', compute='_compute_td_cost', groups=PLAN_GROUPS)
    td_margin_plan_pct = fields.Float(string='Planned Margin, %', compute='_compute_td_cost', digits=(16, 1),
                                      groups=PLAN_GROUPS)
    td_cost_material = fields.Monetary(string='Actual Materials', compute='_compute_td_cost', groups=FACT_GROUPS)
    td_cost_work = fields.Monetary(string='Actual Work', compute='_compute_td_cost', groups=FACT_GROUPS)
    td_cost_cutting = fields.Monetary(string='Cutting', compute='_compute_td_cost', groups=FACT_GROUPS,
                                      help="Purchases of the cutting service from the distributor for the manufacturing "
                                           "orders of the order (a job of several orders is shared by its orders).")
    td_cost_piece = fields.Monetary(string='Piecework', compute='_compute_td_cost', groups=FACT_GROUPS)
    td_cost_crew = fields.Monetary(string='Crew Percent', compute='_compute_td_cost', groups=FACT_GROUPS)
    td_cost_labour = fields.Monetary(string='Piecework and Crew', compute='_compute_td_cost', groups=FACT_GROUPS)
    td_cost_fact = fields.Monetary(string='Actual Cost', compute='_compute_td_cost', groups=FACT_GROUPS)
    td_margin_fact = fields.Monetary(string='Actual Margin', compute='_compute_td_cost', groups=FACT_GROUPS)
    td_margin_fact_pct = fields.Float(string='Actual Margin, %', compute='_compute_td_cost', digits=(16, 1),
                                      groups=FACT_GROUPS)
    td_cost_deviation_pct = fields.Float(string='Cost Deviation, %', compute='_compute_td_cost', digits=(16, 1),
                                         groups=FACT_GROUPS)
    td_cost_has_fact = fields.Boolean(string='Production Finished', compute='_compute_td_cost')
    td_cost_status = fields.Char(string='Actual Status', compute='_compute_td_cost')
    # AC-116: a finished manufacturing order of the order consumed more than its bill of materials
    td_overconsumption = fields.Boolean(string='Overconsumption', compute='_compute_td_overconsumption',
                                        search='_search_td_overconsumption')

    def _td_productions(self):
        """Manufacturing orders of the order, read as the system (the finance has no manufacturing rights)."""
        self.ensure_one()
        return self.sudo().mrp_production_ids

    def _td_actual_cost(self):
        """Actual cost of the finished manufacturing orders of the order, as the standard MO Overview counts it."""
        self.ensure_one()
        material = work = 0.0
        all_productions = self._td_productions()
        productions = all_productions.filtered(lambda p: p.state == 'done')
        for production in productions:
            for move in production.move_raw_ids.filtered(lambda m: m.state == 'done'):
                qty = move.product_uom._compute_quantity(move.quantity, move.product_id.uom_id)
                material += qty * move.product_id.standard_price
            for workorder in production.workorder_ids:
                work += workorder.duration / 60.0 * workorder.workcenter_id.costs_hour
        return bool(productions) and all(p.state == 'done' for p in all_productions), material, work

    def _td_cutting_cost(self):
        """The confirmed purchases of the cutting service of the jobs of the order; a job of several orders is shared
        by the number of its manufacturing orders."""
        self.ensure_one()
        productions = self._td_productions()
        if not productions:
            return 0.0
        jobs = self.env['td.mebli.cutting.job'].sudo().search([('production_ids', 'in', productions.ids),
                                                               ('purchase_id', '!=', False)])
        cost = 0.0
        for job in jobs:
            purchase = job.purchase_id
            if purchase.state not in ('purchase', 'done'):
                continue
            amount = purchase.currency_id._convert(purchase.amount_untaxed, self.currency_id, self.company_id,
                                                   purchase.date_order or fields.Date.today())
            cost += amount * len(job.production_ids & productions) / len(job.production_ids)
        return cost

    def _td_labour_cost(self):
        """Confirmed accruals of the order: (piecework of its manufacturing orders, crew percent of its acts)."""
        self.ensure_one()
        Accrual = self.env['td.mebli.accrual'].sudo()
        productions = self._td_productions()
        piece = Accrual.search([('state', '=', 'confirmed'), ('kind', '=', 'piece'),
                                ('productivity_id.production_id', 'in', productions.ids)]) if productions else Accrual
        crew = Accrual.search([('state', '=', 'confirmed'), ('kind', '=', 'crew'), ('act_id.order_id', '=', self.id)])
        return sum(piece.mapped('amount')), sum(crew.mapped('amount'))

    @api.depends('order_line.purchase_price', 'order_line.product_uom_qty', 'amount_untaxed', 'margin')
    def _compute_td_cost(self):
        for order in self:
            plan = order.amount_untaxed - order.margin
            has_fact, material, work = order._td_actual_cost() if order.id else (False, 0.0, 0.0)
            cutting = order._td_cutting_cost() if has_fact else 0.0
            piece, crew = order._td_labour_cost() if has_fact else (0.0, 0.0)
            piecework = (order.company_id or self.env.company).td_cost_piecework
            fact = material + cutting + crew + (piece if piecework else work) if has_fact else 0.0
            order.td_cost_plan = plan
            order.td_cost_material = material if has_fact else 0.0
            order.td_cost_work = work if has_fact else 0.0
            order.td_cost_cutting = cutting
            order.td_cost_piece = piece
            order.td_cost_crew = crew
            order.td_cost_labour = piece + crew
            order.td_cost_fact = fact
            order.td_cost_has_fact = has_fact
            order.td_cost_status = False if has_fact else self.env._("No actual yet")
            order.td_margin_fact = order.amount_untaxed - fact if has_fact else 0.0
            order.td_margin_plan_pct = order.margin / order.amount_untaxed * 100.0 if order.amount_untaxed else 0.0
            order.td_margin_fact_pct = (order.amount_untaxed - fact) / order.amount_untaxed * 100.0 \
                if has_fact and order.amount_untaxed else 0.0
            order.td_cost_deviation_pct = (fact - plan) / plan * 100.0 if has_fact and plan else 0.0

    # ------------------------------------------------------------------ AC-116: overconsumption
    @api.model
    def _td_overconsumed_productions(self, productions):
        """Done manufacturing orders that consumed more of a component than the bill of materials expects for the
        produced quantity (what the standard consumption warning compares, consumption = 'warning')."""
        over = self.env['mrp.production'].sudo()
        for production in productions.sudo().filtered(lambda p: p.state == 'done' and p.bom_id):
            bom = production.bom_id
            factor = production.product_uom_id._compute_quantity(
                production.qty_produced or production.product_qty, bom.product_uom_id) / (bom.product_qty or 1.0)
            _boms, lines = bom.explode(production.product_id, factor)
            expected = {}
            for line, data in lines:
                qty = line.product_uom_id._compute_quantity(data['qty'], line.product_id.uom_id)
                expected[line.product_id] = expected.get(line.product_id, 0.0) + qty
            consumed = {}
            for move in production.move_raw_ids.filtered(lambda m: m.state == 'done'):
                qty = move.product_uom._compute_quantity(move.quantity, move.product_id.uom_id)
                consumed[move.product_id] = consumed.get(move.product_id, 0.0) + qty
            if any(qty - expected.get(product, 0.0) > product.uom_id.rounding for product, qty in consumed.items()):
                over |= production
        return over

    def _compute_td_overconsumption(self):
        for order in self:
            order.td_overconsumption = bool(order.id and self._td_overconsumed_productions(order._td_productions()))

    def _search_td_overconsumption(self, operator, value):
        if operator not in ('=', '!=') or not isinstance(value, bool):
            return NotImplemented
        productions = self.env['mrp.production'].sudo().search([('state', '=', 'done'), ('bom_id', '!=', False)])
        over = self._td_overconsumed_productions(productions)
        orders = over.reference_ids.sale_ids | over.sale_line_id.order_id
        positive = (operator == '=') == value
        return [('id', 'in' if positive else 'not in', orders.ids)]
