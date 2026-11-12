from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    td_cost_plan = fields.Monetary(string='Planned Cost', compute='_compute_td_cost')
    td_cost_material = fields.Monetary(string='Actual Materials', compute='_compute_td_cost')
    td_cost_work = fields.Monetary(string='Actual Work', compute='_compute_td_cost')
    td_cost_fact = fields.Monetary(string='Actual Cost', compute='_compute_td_cost')
    td_margin_fact = fields.Monetary(string='Actual Margin', compute='_compute_td_cost')
    td_margin_fact_pct = fields.Float(string='Actual Margin, %', compute='_compute_td_cost', digits=(16, 1))
    td_margin_plan_pct = fields.Float(string='Planned Margin, %', compute='_compute_td_cost', digits=(16, 1))
    td_cost_deviation_pct = fields.Float(string='Cost Deviation, %', compute='_compute_td_cost', digits=(16, 1))
    td_cost_has_fact = fields.Boolean(string='Production Finished', compute='_compute_td_cost')

    def _td_actual_cost(self):
        """Actual cost of the finished manufacturing orders of the order, as the standard MO Overview counts it."""
        self.ensure_one()
        material = work = 0.0
        # the salesperson sees the cost of her order without manufacturing rights: the figures are read as the system
        order = self.sudo()
        productions = order.mrp_production_ids.filtered(lambda p: p.state == 'done')
        for production in productions:
            for move in production.move_raw_ids.filtered(lambda m: m.state == 'done'):
                qty = move.product_uom._compute_quantity(move.quantity, move.product_id.uom_id)
                material += qty * move.product_id.standard_price
            for workorder in production.workorder_ids:
                work += workorder.duration / 60.0 * workorder.workcenter_id.costs_hour
        return bool(productions) and all(p.state == 'done' for p in order.mrp_production_ids), material, work

    @api.depends('order_line.purchase_price', 'order_line.product_uom_qty', 'amount_untaxed', 'margin')
    def _compute_td_cost(self):
        for order in self:
            plan = order.amount_untaxed - order.margin
            has_fact, material, work = order._td_actual_cost()
            fact = material + work if has_fact else 0.0
            order.td_cost_plan = plan
            order.td_cost_material = material if has_fact else 0.0
            order.td_cost_work = work if has_fact else 0.0
            order.td_cost_fact = fact
            order.td_cost_has_fact = has_fact
            order.td_margin_fact = order.amount_untaxed - fact if has_fact else 0.0
            order.td_margin_plan_pct = order.margin / order.amount_untaxed * 100.0 if order.amount_untaxed else 0.0
            order.td_margin_fact_pct = (order.amount_untaxed - fact) / order.amount_untaxed * 100.0 \
                if has_fact and order.amount_untaxed else 0.0
            order.td_cost_deviation_pct = (fact - plan) / plan * 100.0 if has_fact and plan else 0.0
