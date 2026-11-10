from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError
from odoo.tools.misc import formatLang

PERIOD_DAYS = 30
LOW_MARGIN = 0.15      # the same threshold as the red rows of the margin report (td_mebli_sale)
TARGET_LAUNCH_H = 48   # order to launch, hours
TARGET_WASTE_PCT = 8   # cutting waste, %
TARGET_OVERRUN_PCT = 3  # cost overrun against the plan, %
GROUP = 'td_mebli_dashboard.group_td_mebli_director'


class TdMebliDashboard(models.AbstractModel):
    _name = 'td.mebli.dashboard'
    _description = 'Manager Dashboard of the Furniture Factory'

    @api.model
    def _money(self, value):
        symbol = self.env.company.currency_id.symbol
        return f"{round(value):,}".replace(',', ' ') + f" {symbol}"

    @api.model
    def _num(self, value, digits=1):
        return formatLang(self.env, value, digits=digits)

    @api.model
    def _delta(self, cur, prev, kind, good_when_up=True):
        """Comparison with the previous period: kind 'pct' (relative change) or 'pp' (difference in points)."""
        _ = self.env._
        if not prev:
            return {'text': _("no data for the previous %s days", PERIOD_DAYS), 'tone': 'flat'}
        change = (cur - prev) / abs(prev) * 100.0 if kind == 'pct' else cur - prev
        sign = '+' if change > 0 else ''
        unit = '%' if kind == 'pct' else _("p.p.")
        tone = 'flat' if abs(change) < 0.05 else ('ok' if (change > 0) == good_when_up else 'bad')
        arrow = '▲' if change > 0 else ('▼' if change < 0 else '■')
        return {'text': _("%s %s%s %s vs previous %s days", arrow, sign, self._num(change), unit, PERIOD_DAYS), 'tone': tone}

    @api.model
    def _orders_stats(self, env, company, start, end):
        orders = env['sale.order'].with_context(active_test=False).search([
            ('state', '=', 'sale'), ('date_order', '>=', start), ('date_order', '<', end), ('company_id', '=', company.id)])
        revenue = sum(orders.mapped('amount_untaxed'))
        margin = sum(orders.mapped('margin'))
        hours = [o.td_hours_to_launch for o in orders.filtered('td_launch_date')]
        return {
            'orders': orders, 'revenue': revenue, 'margin': margin,
            'margin_pct': margin / revenue * 100.0 if revenue else 0.0,
            'launch_avg': sum(hours) / len(hours) if hours else 0.0, 'launched': len(hours),
        }

    @api.model
    def _cutting_stats(self, env, company, start, end):
        jobs = env['td.mebli.cutting.job'].search([
            ('state', 'in', ('result', 'done')), ('company_id', '=', company.id),
            ('create_date', '>=', start), ('create_date', '<', end)])
        sheets = jobs.sheet_ids
        area = sum(sheets.mapped('used_area_m2')) + sum(sheets.mapped('offcut_area_m2'))
        waste = sum(s.waste_pct * (s.used_area_m2 + s.offcut_area_m2) for s in sheets)
        return {'jobs': jobs, 'waste_pct': waste / area if area else 0.0, 'saving': sum(jobs.mapped('offcut_saving'))}

    @api.model
    def get_data(self):
        """All figures of the screen in one call. Computed with sudo (the manager sees the whole factory), so the call
        itself is limited to the director group and the administrators."""
        user = self.env.user
        if not (self.env.su or user.has_group(GROUP) or user.has_group('base.group_system')):
            raise AccessError(self.env._("The factory dashboard is available to the factory director only."))
        env = self.sudo().with_company(self.env.company).env
        company = env.company
        now = fields.Datetime.now()
        since = now - timedelta(days=PERIOD_DAYS)
        before = since - timedelta(days=PERIOD_DAYS)
        cur = self._orders_stats(env, company, since, now + timedelta(days=1))
        prev = self._orders_stats(env, company, before, since)
        orders = cur['orders']
        quotes = env['sale.order'].with_context(active_test=False).search([
            ('state', 'in', ('draft', 'sent')), ('company_id', '=', company.id)])
        low = orders.filtered(lambda o: o.amount_untaxed and o.margin / o.amount_untaxed < LOW_MARGIN)
        low = low.sorted(lambda o: o.margin / o.amount_untaxed)
        launched_count = cur['launched']
        waiting = len(orders) - launched_count

        load = []
        for center in env['mrp.workcenter'].search([('td_capacity_hours', '>', 0)]):
            planned = sum(center.order_ids.filtered(lambda w: w.state not in ('done', 'cancel')).mapped('duration_expected')) / 60.0
            if planned:
                load.append({'name': center.name, 'pct': round(planned / center.td_capacity_hours * 100.0),
                             'over': planned > center.td_capacity_hours})
        load.sort(key=lambda row: -row['pct'])

        cut = self._cutting_stats(env, company, since, now + timedelta(days=1))
        cut_prev = self._cutting_stats(env, company, before, since)
        offcut_area = sum(lot.td_area_m2 for lot in env['stock.lot'].search([('td_is_offcut', '=', True)]) if lot.product_qty > 0)

        plan_materials = plan_work = fact_materials = fact_work = 0.0
        done = env['mrp.production'].search([('state', '=', 'done'), ('company_id', '=', company.id),
                                             ('date_finished', '>=', since)])
        for line in done.sale_line_id:
            plan_materials += line.td_planned_material_cost
            plan_work += line.td_planned_operation_cost
            for production in done.filtered(lambda p: p.sale_line_id == line):
                for move in production.move_raw_ids.filtered(lambda m: m.state == 'done'):
                    fact_materials += move.product_uom._compute_quantity(move.quantity, move.product_id.uom_id) * move.product_id.standard_price
                for wo in production.workorder_ids:
                    fact_work += wo.duration / 60.0 * wo.workcenter_id.costs_hour
        plan = plan_materials + plan_work
        fact = fact_materials + fact_work
        deviation = (fact - plan) / plan * 100.0 if plan else 0.0

        _ = self.env._
        margin_tone = 'bad' if cur['margin_pct'] < 20 else ('warn' if low else 'ok')
        note = env['ir.config_parameter'].get_param('td_mebli_dashboard.note') or \
            _("Plan margin: standard prices of materials and hours.")
        return {
            'title': _("Factory on one screen"),
            'period': _("Last %s days · %s", PERIOD_DAYS, fields.Date.context_today(self).strftime('%d.%m.%Y')),
            'company': company.name,
            'cards': {
                'revenue': {
                    'label': _("Revenue"), 'value': self._money(cur['revenue']),
                    'delta': self._delta(cur['revenue'], prev['revenue'], 'pct'),
                    'lines': [_("Orders confirmed: %s (previous period: %s)", len(orders), len(prev['orders'])),
                              _("In quotations: %s for %s", len(quotes), self._money(sum(quotes.mapped('amount_untaxed'))))],
                    'action': 'td_mebli_sale.action_orders_board_td_mebli',
                },
                'margin': {
                    'label': _("Average margin"), 'value': f"{self._num(cur['margin_pct'])} %", 'tone': margin_tone,
                    'delta': self._delta(cur['margin_pct'], prev['margin_pct'], 'pp'),
                    'alert': _("Orders below %s%%: %s", int(LOW_MARGIN * 100), len(low)) if low else '',
                    'alert_rows': [f"{o.name} · {self._num(o.margin / o.amount_untaxed * 100)} %" for o in low[:3]],
                    'lines': [_("Margin: %s of %s", self._money(cur['margin']), self._money(cur['revenue']))],
                    'action': 'td_mebli_sale.sale_order_line_td_cost_action',
                },
                'launch': {
                    'label': _("Order to launch"), 'value': _("%s h", self._num(cur['launch_avg'])),
                    'tone': 'ok' if cur['launch_avg'] <= TARGET_LAUNCH_H else 'warn',
                    'target': _("Target: up to %s h", TARGET_LAUNCH_H),
                    'delta': self._delta(cur['launch_avg'], prev['launch_avg'], 'pct', good_when_up=False),
                    'lines': [_("Average for %s launched orders", launched_count),
                              _("Waiting for launch: %s", waiting)],
                    'action': 'td_mebli_sale.action_orders_launch_td_mebli',
                },
                'load': {
                    'label': _("Section load, % of week"), 'rows': load,
                    'target': _("Over 100%: the section is the bottleneck"),
                    'lines': [_("Over capacity: %s", sum(1 for row in load if row['over']))],
                    'action': 'td_mebli_mrp.mrp_workorder_td_load_action',
                },
                'cutting': {
                    'label': _("Cutting waste"), 'value': f"{self._num(cut['waste_pct'])} %",
                    'tone': 'ok' if cut['waste_pct'] <= TARGET_WASTE_PCT else 'warn',
                    'target': _("Target: up to %s%%", TARGET_WASTE_PCT),
                    'delta': self._delta(cut['waste_pct'], cut_prev['waste_pct'], 'pp', good_when_up=False),
                    'lines': [_("Saved by business offcuts: %s", self._money(cut['saving'])),
                              _("Offcuts in stock: %s m²", self._num(offcut_area)),
                              _("Cutting jobs: %s", len(cut['jobs']))],
                    'action': 'td_mebli_cutting.td_mebli_cutting_job_action',
                },
                'plan_fact': {
                    'label': _("Cost: plan vs actual"), 'value': f"{'+' if deviation > 0 else ''}{self._num(deviation)} %",
                    'tone': 'ok' if deviation <= 0 else ('warn' if deviation <= TARGET_OVERRUN_PCT else 'bad'),
                    'target': _("Target: overrun up to %s%%", TARGET_OVERRUN_PCT),
                    'plan': self._money(plan), 'fact': self._money(fact),
                    'plan_label': _("Plan"), 'fact_label': _("Actual"),
                    'fact_ratio': round(min(fact / plan, 1.5) / 1.5 * 100.0) if plan else 0,
                    'plan_ratio': round(1 / 1.5 * 100.0) if plan else 0,
                    'lines': [_("Manufacturing orders finished: %s", len(done))],
                    'action': 'mrp.mrp_production_action',
                },
            },
            'note': note,
        }
