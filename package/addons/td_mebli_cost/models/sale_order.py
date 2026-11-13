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
        # sudo: read only: the finance has no manufacturing rights
        return self.sudo().mrp_production_ids

    def _td_actual_cost(self):
        """Actual cost of the finished manufacturing orders of the order, as the standard MO Overview counts it."""
        self.ensure_one()
        return self._td_actual_costs()[self.id]

    def _td_actual_costs(self):
        """{order id: (has fact, material, work)} for the whole recordset: the manufacturing orders, their moves and
        work orders are read in batches (prefetch of the recordset), not order by order (review A-11, N+1)."""
        result = {}
        # sudo: read only: the cost report reads manufacturing and stock for the finance
        orders = self.sudo()
        all_productions = orders.mrp_production_ids
        all_productions.move_raw_ids.mapped('quantity')  # one prefetch of the moves and the work orders of the batch
        all_productions.workorder_ids.mapped('duration')
        for order in orders:
            productions = order.mrp_production_ids
            done = productions.filtered(lambda p: p.state == 'done')
            material = work = 0.0
            for production in done:
                for move in production.move_raw_ids.filtered(lambda m: m.state == 'done'):
                    qty = move.product_uom._compute_quantity(move.quantity, move.product_id.uom_id)
                    material += qty * move.product_id.standard_price
                for workorder in production.workorder_ids:
                    work += workorder.duration / 60.0 * workorder.workcenter_id.costs_hour
            result[order.id] = (bool(done) and all(p.state == 'done' for p in productions), material, work)
        return result

    def _td_cutting_cost(self):
        """The confirmed purchases of the cutting service of the jobs of the order; a job of several orders is shared
        by the number of its manufacturing orders."""
        self.ensure_one()
        return self._td_cutting_costs()[self.id]

    def _td_cutting_costs(self):
        """{order id: cutting cost} with one search of the jobs for the whole recordset."""
        # sudo: read only: the cost report reads the cutting jobs for the finance
        orders = self.sudo()
        result = dict.fromkeys(self.ids, 0.0)
        productions = orders.mrp_production_ids
        if not productions:
            return result
        # sudo: read only: the cost report reads the cutting jobs for the finance
        jobs = self.env['td.mebli.cutting.job'].sudo().search([('production_ids', 'in', productions.ids),
                                                               ('purchase_id', '!=', False),
                                                               ('purchase_id.state', 'in', ('purchase', 'done'))])
        for order in orders:
            own = order.mrp_production_ids
            for job in jobs.filtered(lambda j: j.production_ids & own):
                purchase = job.purchase_id
                amount = purchase.currency_id._convert(purchase.amount_untaxed, order.currency_id, order.company_id,
                                                       purchase.date_order or fields.Date.today())
                result[order.id] += amount * len(job.production_ids & own) / len(job.production_ids)
        return result

    def _td_labour_cost(self):
        """Confirmed accruals of the order: (piecework of its manufacturing orders, crew percent of its acts)."""
        self.ensure_one()
        return self._td_labour_costs()[self.id]

    def _td_labour_costs(self):
        """{order id: (piecework, crew)} with two searches of the accruals for the whole recordset."""
        # sudo: read only: the cost report reads the accruals of all the employees for the finance
        orders = self.sudo()
        result = {order_id: [0.0, 0.0] for order_id in self.ids}
        # sudo: read only: the cost report reads the accruals of all the employees for the finance
        Accrual = self.env['td.mebli.accrual'].sudo()
        productions = orders.mrp_production_ids
        if productions:
            by_production = {production.id: order.id for order in orders for production in order.mrp_production_ids}
            for accrual in Accrual.search([('state', '=', 'confirmed'), ('kind', '=', 'piece'),
                                           ('productivity_id.production_id', 'in', productions.ids)]):
                result[by_production[accrual.productivity_id.production_id.id]][0] += accrual.amount
        for accrual in Accrual.search([('state', '=', 'confirmed'), ('kind', '=', 'crew'),
                                       ('act_id.order_id', 'in', self.ids)]):
            result[accrual.act_id.order_id.id][1] += accrual.amount
        return {order_id: tuple(values) for order_id, values in result.items()}

    @api.depends('order_line.purchase_price', 'order_line.product_uom_qty', 'amount_untaxed', 'margin')
    def _compute_td_cost(self):
        real = self.filtered('id')
        actual = real._td_actual_costs()
        with_fact = real.filtered(lambda o: actual[o.id][0])
        cuttings = with_fact._td_cutting_costs()
        labours = with_fact._td_labour_costs()
        for order in self:
            plan = order.amount_untaxed - order.margin
            has_fact, material, work = actual.get(order.id, (False, 0.0, 0.0))
            cutting = cuttings.get(order.id, 0.0)
            piece, crew = labours.get(order.id, (0.0, 0.0))
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
        produced quantity — the stored flag of the manufacturing order (computed once, when it is done)."""
        # sudo: read only: the stored overconsumption flag of the manufacturing orders
        return productions.sudo().filtered('td_overconsumed')

    def _compute_td_overconsumption(self):
        for order in self:
            order.td_overconsumption = bool(order.id and self._td_overconsumed_productions(order._td_productions()))

    def _search_td_overconsumption(self, operator, value):
        """Review A-11: the stored flag of the manufacturing orders of the allowed companies — no scan of the whole
        history of the done manufacturing orders at every search."""
        if operator not in ('=', '!=') or not isinstance(value, bool):
            return NotImplemented
        # sudo: read only: the search of the flag; the result is the sale orders the user reads
        over = self.env['mrp.production'].sudo().search([('td_overconsumed', '=', True),
                                                         ('company_id', 'in', self.env.companies.ids)])
        orders = over.reference_ids.sale_ids | over.sale_line_id.order_id
        positive = (operator == '=') == value
        return [('id', 'in' if positive else 'not in', orders.ids)]


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # AC-116 (review A-11): computed when the manufacturing order is done (or its consumption changes), searched by
    # the filter «Overconsumption» of the orders
    td_overconsumed = fields.Boolean(string='Overconsumption', compute='_compute_td_overconsumed', store=True,
                                     copy=False)

    @api.depends('state', 'bom_id', 'qty_produced', 'product_qty', 'move_raw_ids.state', 'move_raw_ids.quantity')
    def _compute_td_overconsumed(self):
        """More of a component than the bill of materials expects for the produced quantity (what the standard
        consumption warning compares, consumption = 'warning')."""
        for production in self:
            production.td_overconsumed = production.state == 'done' and bool(production.bom_id) \
                and production._td_is_overconsumed()

    def _td_is_overconsumed(self):
        self.ensure_one()
        bom = self.bom_id
        factor = self.product_uom_id._compute_quantity(
            self.qty_produced or self.product_qty, bom.product_uom_id) / (bom.product_qty or 1.0)
        _boms, lines = bom.explode(self.product_id, factor)
        expected = {}
        for line, data in lines:
            qty = line.product_uom_id._compute_quantity(data['qty'], line.product_id.uom_id)
            expected[line.product_id] = expected.get(line.product_id, 0.0) + qty
        consumed = {}
        for move in self.move_raw_ids.filtered(lambda m: m.state == 'done'):
            qty = move.product_uom._compute_quantity(move.quantity, move.product_id.uom_id)
            consumed[move.product_id] = consumed.get(move.product_id, 0.0) + qty
        return any(qty - expected.get(product, 0.0) > product.uom_id.rounding for product, qty in consumed.items())
