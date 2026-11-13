from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError
from odoo.tools.misc import formatLang

PERIOD_DAYS = 30
LOW_MARGIN = 0.15        # the same threshold as the red rows of the margin report (td_mebli_sale)
TARGET_ON_TIME = 90      # % of installed orders on the promised date
TARGET_WASTE_PCT = 8     # cutting waste, %
TARGET_CLAIMS = 5        # claims per 100 installed orders
GROUP = 'td_mebli_dashboard.group_td_mebli_director'
QUALITY_FEATURE = 'td_mebli_base.group_feature_quality'  # the 12th card (box B/C, VP-02)


class TdMebliDashboard(models.AbstractModel):
    _name = 'td.mebli.dashboard'
    _description = 'Manager Dashboard of the Furniture Factory'

    # ---------------------------------------------------------------- formatting
    @api.model
    def _money(self, value):
        symbol = self.env.company.currency_id.symbol
        sign = '−' if value < 0 else ''
        return sign + f"{round(abs(value)):,}".replace(',', ' ') + f" {symbol}"

    @api.model
    def _num(self, value, digits=1):
        return formatLang(self.env, value, digits=digits)

    @api.model
    def _pct(self, value):
        return f"{self._num(value)} %"

    @api.model
    def _no_data(self):
        """AC-123: a card without data says so (no «0 %» from a division by zero)."""
        return self.env._("No data")

    @api.model
    def _drill(self, name, model, records, *views):
        """Drill-down of a card: exactly the records the card counted (the totals of the report equal the card)."""
        # sudo: read only: the id of a view (ir.ui.view is admin only)
        view_list = [[self.env.ref(xmlid).sudo().id if xmlid else False, kind] for kind, xmlid in views]
        if not any(kind == 'form' for kind, _x in views):
            view_list.append([False, 'form'])
        return {'name': name, 'res_model': model, 'ids': records.ids, 'views': view_list}

    # ---------------------------------------------------------------- figures
    @api.model
    def _period(self):
        today = fields.Date.context_today(self)
        since = fields.Datetime.to_datetime(today - timedelta(days=PERIOD_DAYS))
        return today, since

    @api.model
    def _final_acts(self, env, since):
        return env['td.mebli.install.act'].search([('kind', '=', 'final'), ('state', '=', 'signed'),
                                                   ('company_id', 'in', self._company_ids(env)),
                                                   ('signed_on', '>=', since)])

    @api.model
    def _company_ids(self, env):
        """The companies of the cards: the companies selected by the director (self.env.companies before sudo, kept in
        the context of get_data), never the whole database — sudo would otherwise ignore the multi-company rules."""
        return env.context.get('td_dash_company_ids') or env.company.ids

    @api.model
    def _card_on_time(self, env, since):
        _ = self.env._
        acts = self._final_acts(env, since)
        orders = acts.order_id
        on_time = orders.filtered(lambda o: o.commitment_date and min(
            acts.filtered(lambda a: a.order_id == o).mapped('signed_on')).date() <= o.commitment_date.date())
        pct = len(on_time) / len(orders) * 100.0 if orders else 0.0
        return {'label': _("Orders on time"), 'value': self._pct(pct) if orders else self._no_data(),
                'tone': 'ok' if pct >= TARGET_ON_TIME else ('warn' if pct >= TARGET_ON_TIME - 15 else 'bad'),
                'target': _("Target: from %s%%", TARGET_ON_TIME),
                'lines': [_("Installed: %(all)s, on the promised date: %(ok)s", all=len(orders), ok=len(on_time))],
                'drill': self._drill(_("Installed orders"), 'sale.order', orders,
                                     ('list', 'td_mebli_dashboard.sale_order_td_dash_list'))}

    @api.model
    def _card_shift(self, env, company, since):
        _ = self.env._
        open_orders = env['sale.order'].search([('state', '=', 'sale'), ('company_id', 'in', self._company_ids(env))])
        # open = not delivered in full yet (delivered orders keep their old dates, they are not «at risk»)
        late = open_orders.filtered(lambda o: o.td_delay_days > 0 and o.delivery_status != 'full')
        changes = env['td.mebli.order.change'].search([('state', '=', 'done'), ('shift_days', '>', 0),
                                                       ('company_id', 'in', self._company_ids(env)),
                                                       ('write_date', '>=', since)])
        reasons = {'customer': [0, set()], 'company': [0, set()], 'supplier': [0, set()], 'distributor': [0, set()]}
        for order in late:
            reasons[order.td_delay_reason or 'company'][0] += order.td_delay_days
            reasons[order.td_delay_reason or 'company'][1].add(order.id)
        for change in changes:
            reasons[change.reason][0] += change.shift_days
            reasons[change.reason][1].add(change.order_id.id)
        names = {'customer': _("Customer"), 'company': _("Company"), 'supplier': _("Supplier"),
                 'distributor': _("Cutting at the distributor")}
        total = sum(days for days, _ids in reasons.values()) or 1
        rows = [{'name': names[key], 'value': _("%s d.", days), 'pct': round(days / total * 100), 'over': key == 'company'}
                for key, (days, ids) in reasons.items() if days]
        ids = set().union(*(ids for _days, ids in reasons.values()))
        orders = env['sale.order'].browse(sorted(ids))
        return {'label': _("Date shift by reason"), 'value': _("%s orders", len(orders)), 'tone': 'warn' if late else 'ok',
                'target': _("Days of shift of the promised dates"), 'rows': rows,
                'lines': [_("Now at risk: %s", len(late))],
                'drill': self._drill(_("Orders with a shifted date"), 'sale.order', orders,
                                     ('list', 'td_mebli_dashboard.sale_order_td_dash_list'))}

    @api.model
    def _card_stuck(self, env, company):
        _ = self.env._
        stuck_days = company.td_stuck_days  # VP-10 (td_mebli_base), read by the search of td_is_stuck
        # AC-067: the stored flag of the order (td_mebli_sale) — a confirmed order whose stage did not move for longer
        stuck = env['sale.order'].search([('td_is_stuck', '=', True), ('company_id', 'in', self._company_ids(env))])
        return {'label': _("Stuck orders"), 'value': str(len(stuck)), 'tone': 'bad' if stuck else 'ok',
                'target': _("No change of the stage for more than %s days", stuck_days),
                'lines': [f"{o.name} · {o.partner_id.name}" for o in stuck[:3]],
                'drill': self._drill(_("Stuck orders"), 'sale.order', stuck,
                                     ('list', 'td_mebli_dashboard.sale_order_td_dash_list'))}

    @api.model
    def _card_payments(self, env):
        """Payments due: after a signed final act (the card value, the drill-down) and, as a line, the coming visits
        of the made orders that are not paid before the installation (the same control as on the visit, F-22)."""
        _ = self.env._
        company_ids = self._company_ids(env)
        acts = env['td.mebli.install.act'].search([('kind', '=', 'final'), ('state', '=', 'signed'),
                                                   ('company_id', 'in', company_ids)])
        orders = acts.order_id.filtered(lambda o: o.td_dash_due > 0.5)
        due = sum(orders.mapped('td_dash_due'))
        visits = env['project.task'].search([('sale_order_id', '!=', False), ('state', 'not in', ('1_done', '1_canceled')),
                                             ('sale_order_id.state', '=', 'sale'),
                                             ('sale_order_id.company_id', 'in', company_ids)])
        unpaid = visits.sale_order_id.filtered(
            lambda o: o.td_stage in ('done', 'wait', 'shipped', 'install') and not o.td_pay_ok
            and not o.td_act_ids.filtered(lambda a: a.kind == 'final' and a.state == 'signed'))
        return {'label': _("Payments due after installation"), 'value': self._money(due),
                'tone': 'warn' if due or unpaid else 'ok', 'target': _("Signed final act, the customer has not paid in full"),
                'lines': [_("Orders: %s", len(orders)),
                          _("Before installation without payment: %s", len(unpaid))],
                'drill': self._drill(_("Payments due after installation"), 'sale.order', orders,
                                     ('list', 'td_mebli_dashboard.sale_order_td_dash_due_list'))}

    @api.model
    def _card_claims(self, env, since):
        _ = self.env._
        claims = env['repair.order'].search([('td_claim_order_id', '!=', False), ('create_date', '>=', since),
                                             ('company_id', 'in', self._company_ids(env))])
        installed = len(self._final_acts(env, since).order_id)
        per100 = len(claims) / installed * 100.0 if installed else 0.0
        closed = claims.filtered(lambda r: r.state == 'done')
        avg_days = sum(closed.mapped('td_days_open')) / len(closed) if closed else 0.0
        overdue = claims.filtered('td_overdue')
        return {'label': _("Claims per 100 orders"), 'value': self._num(per100) if installed else self._no_data(),
                'tone': 'ok' if per100 <= TARGET_CLAIMS else 'bad', 'target': _("Target: up to %s", TARGET_CLAIMS),
                'lines': [_("Claims: %(claims)s for %(installed)s installed", claims=len(claims), installed=installed),
                          _("Closed on average in %s days", self._num(avg_days)), _("Overdue: %s", len(overdue))],
                'drill': self._drill(_("Claims"), 'repair.order', claims,
                                     ('list', 'td_mebli_claim.view_repair_list_td_mebli'))}

    @api.model
    def _card_margin(self, env, company, since):
        _ = self.env._
        orders = env['sale.order'].search([('state', '=', 'sale'), ('company_id', 'in', self._company_ids(env)),
                                           ('date_order', '>=', since)])
        revenue, margin = sum(orders.mapped('amount_untaxed')), sum(orders.mapped('margin'))
        pct = margin / revenue * 100.0 if revenue else 0.0
        low = orders.filtered(lambda o: o.amount_untaxed and o.margin / o.amount_untaxed < LOW_MARGIN)
        # one figure: the weighted margin of the confirmed orders; plan vs actual of the finished orders is the
        # report S-11 «Cost: plan vs actual» (the drill-down list), not a second figure on the card
        lines = [_("Margin %(margin)s of revenue %(revenue)s, %(count)s orders", margin=self._money(margin),
                   revenue=self._money(revenue), count=len(orders))]
        return {'label': _("Margin, weighted"), 'value': self._pct(pct) if revenue else self._no_data(),
                'tone': 'bad' if pct < 20 else ('warn' if low else 'ok'),
                'target': _("Total margin ÷ total revenue of the report, %s days", PERIOD_DAYS),
                'lines': lines,
                'alert': _("Below %(pct)s%%: %(count)s", pct=int(LOW_MARGIN * 100), count=len(low)) if low else '',
                'alert_rows': [f"{o.name} · {self._pct(o.margin / o.amount_untaxed * 100)}" for o in low[:2]],
                'drill': self._drill(_("Margin of the orders"), 'sale.order', orders,
                                     ('list', 'td_mebli_dashboard.sale_order_td_dash_margin_list'))}

    @api.model
    def _week(self):
        """The next 7 days: the work that is open and planned to start before their end."""
        start = fields.Datetime.to_datetime(fields.Date.context_today(self))
        return start, start + timedelta(days=7)

    @api.model
    def _card_load(self, env):
        _ = self.env._
        start, end = self._week()
        company_ids = self._company_ids(env)
        centers = env['mrp.workcenter'].search([('company_id', 'in', company_ids + [False])])
        week = env['mrp.workorder'].search([('state', 'not in', ('done', 'cancel')), ('date_start', '!=', False),
                                            ('date_start', '<', end), ('production_id.company_id', 'in', company_ids)])
        rows, over = [], 0
        for center in centers.filtered(lambda c: c.td_capacity_hours > 0):
            hours = sum(week.filtered(lambda w: w.workcenter_id == center).mapped('td_expected_hours'))
            if hours:
                pct = round(hours / center.td_capacity_hours * 100.0)
                rows.append({'name': center.name, 'pct': pct, 'value': f"{pct}%", 'over': pct > 100})
                over += pct > 100
        rows.sort(key=lambda row: -row['pct'])
        queue = env['mrp.workorder'].search([('state', 'not in', ('done', 'cancel')),
                                             ('production_id.company_id', 'in', company_ids)])
        capacity = sum(centers.mapped('td_capacity_hours'))
        weeks = sum(queue.mapped('td_expected_hours')) / capacity if capacity else 0.0
        return {'label': _("Section load, 7 days"), 'rows': rows,
                'target': _("Open work started or planned to start in 7 days ÷ weekly hours of the section calendar"),
                'lines': [_("Over capacity: %s", over), _("Open queue: %s weeks of work", self._num(weeks))],
                'drill': self._drill(_("Section load, 7 days"), 'mrp.workorder', week,
                                     ('pivot', 'td_mebli_mrp.mrp_workorder_td_load_pivot'),
                                     ('list', 'td_mebli_shop.mrp_workorder_td_tablet_list'))}

    @api.model
    def _card_conversion(self, env, since):
        _ = self.env._
        sheets = env['td.mebli.measure'].search([('create_date', '>=', since),
                                                 ('company_id', 'in', self._company_ids(env))])
        signed = sheets.filtered(lambda s: s.order_id.state == 'sale')
        pct = len(signed) / len(sheets) * 100.0 if sheets else 0.0
        return {'label': _("Measurement to contract"), 'value': self._pct(pct) if sheets else self._no_data(),
                'tone': 'ok' if pct >= 50 else 'warn',
                'target': _("Measurements of %s days that became confirmed orders", PERIOD_DAYS),
                'lines': [_("Measurements: %(all)s, contracts: %(ok)s", all=len(sheets), ok=len(signed))],
                'drill': self._drill(_("Measurements"), 'td.mebli.measure', sheets,
                                     ('list', 'td_mebli_measure.td_mebli_measure_view_list'))}

    @api.model
    def _card_ready(self, env, company):
        _ = self.env._
        now = fields.Datetime.now()
        ready = env['sale.order'].search([('state', '=', 'sale'), ('company_id', 'in', self._company_ids(env))]).filtered(
            lambda o: o.mrp_production_ids and all(p.state == 'done' for p in o.mrp_production_ids)
            and o.picking_ids.filtered(lambda p: p.picking_type_code == 'outgoing' and p.state not in ('done', 'cancel')))
        days = [(now - max(o.mrp_production_ids.mapped('date_finished'))).days for o in ready]
        return {'label': _("Ready, not shipped"), 'value': str(len(ready)), 'tone': 'warn' if ready else 'ok',
                'target': _("Production finished, the delivery is not done"),
                'lines': [_("For %s", self._money(sum(ready.mapped('amount_untaxed')))),
                          _("In the warehouse on average %s days", self._num(sum(days) / len(days) if days else 0.0))],
                'drill': self._drill(_("Ready, not shipped"), 'sale.order', ready,
                                     ('list', 'td_mebli_dashboard.sale_order_td_dash_list'))}

    @api.model
    def _card_waste(self, env, company, since):
        _ = self.env._
        jobs = env['td.mebli.cutting.job'].search([('state', 'in', ('result', 'done')), ('company_id', 'in', self._company_ids(env)),
                                                   ('create_date', '>=', since)])
        sheets = jobs.sheet_ids
        area = sum(sheets.mapped('used_area_m2')) + sum(sheets.mapped('offcut_area_m2'))
        waste = sum(s.waste_pct * (s.used_area_m2 + s.offcut_area_m2) for s in sheets) / area if area else 0.0
        return {'label': _("Cutting waste"), 'value': self._pct(waste) if area else self._no_data(),
                'tone': 'ok' if waste <= TARGET_WASTE_PCT else 'warn', 'target': _("Target: up to %s%%", TARGET_WASTE_PCT),
                'lines': [_("Saved by business offcuts: %s", self._money(sum(jobs.mapped('offcut_saving')))),
                          _("Cutting jobs: %s", len(jobs))],
                'drill': self._drill(_("Cutting jobs"), 'td.mebli.cutting.job', jobs,
                                     ('list', 'td_mebli_cutting.td_mebli_cutting_job_view_list'))}

    @api.model
    def _card_prices(self, env, company, since):
        _ = self.env._
        lines = env['purchase.order.line'].search([('company_id', 'in', self._company_ids(env)), ('state', 'in', ('purchase', 'done')),
                                                   ('order_id.date_order', '>=', since), ('td_over_history', '=', True)])
        overpay = sum(lines.mapped('td_overpay'))
        return {'label': _("Supplier prices above history"), 'value': self._money(overpay),
                'tone': 'warn' if lines else 'ok', 'target': _("Overpay against the average of 180 days"),
                'lines': [_("Purchase lines: %s", len(lines))] + [
                    f"{ln.product_id.name} · +{self._num(ln.td_price_delta_pct)} %" for ln in lines.sorted('td_overpay', reverse=True)[:2]],
                'drill': self._drill(_("Prices above history"), 'purchase.order.line', lines,
                                     ('list', 'td_mebli_purchase.purchase_order_line_td_price_list'))}

    @api.model
    def _card_quality(self, env, company, since):
        """Card 12 (box B/C, `group_feature_quality`): the failed quality checks of the tablet in the period — the
        nonconformities and the defects of the shop; the drill-down is the same records."""
        _ = self.env._
        # AC-073 + AC-121: failed quality steps (kind «check») and scraps of the shop (kind «scrap») are the journal
        checks = env['td.mebli.quality.check'].search([('result', '=', 'fail'), ('create_date', '>=', since),
                                                       ('company_id', 'in', self._company_ids(env))])
        scraps = len(checks.filtered(lambda check: check.kind == 'scrap'))
        by_center = {}
        for check in checks:
            by_center[check.workcenter_id.name or _("Without a work center")] = \
                by_center.get(check.workcenter_id.name or _("Without a work center"), 0) + 1
        rows = [{'name': name, 'value': str(count), 'pct': round(count / len(checks) * 100), 'over': False}
                for name, count in sorted(by_center.items(), key=lambda item: -item[1])[:4]]
        return {'label': _("Quality nonconformities"), 'value': str(len(checks)), 'tone': 'bad' if checks else 'ok',
                'target': _("Failed quality checks and defects of the shop, %s days", PERIOD_DAYS), 'rows': rows,
                'lines': [_("Manufacturing orders: %s", len(checks.production_id)), _("Scraps: %s", scraps)],
                'drill': self._drill(_("Quality nonconformities"), 'td.mebli.quality.check', checks,
                                     ('list', 'td_mebli_shop.td_mebli_quality_check_view_list'))}

    @api.model
    def get_data(self):
        """All figures of the screen in one call. Computed with sudo (the owner sees the whole factory), so the call
        itself is limited to the director group and the administrators."""
        user = self.env.user
        if not (self.env.su or user.has_group(GROUP) or user.has_group('base.group_system')):
            raise AccessError(self.env._("The factory dashboard is available to the factory director only."))
        # the companies the director works in now (validated against the user's companies before sudo)
        company_ids = self.env.companies.ids
        # sudo: read only: the cards count over modules the director has no rights on, in his companies only
        env = self.sudo().with_company(self.env.company).with_context(td_dash_company_ids=company_ids).env
        company = env.company
        today, since = self._period()
        _ = self.env._
        cards = [
            ('shift', self._card_shift(env, company, since)),
            ('on_time', self._card_on_time(env, since)),
            ('stuck', self._card_stuck(env, company)),
            ('margin', self._card_margin(env, company, since)),
            ('claims', self._card_claims(env, since)),
            ('payments', self._card_payments(env)),
            ('prices', self._card_prices(env, company, since)),
            ('load', self._card_load(env)),
            ('ready', self._card_ready(env, company)),
            ('conversion', self._card_conversion(env, since)),
            ('waste', self._card_waste(env, company, since)),
        ]
        if user.has_group(QUALITY_FEATURE):  # box B/C: the 12th card (AC-121)
            cards.append(('quality', self._card_quality(env, company, since)))
        for key, card in cards:
            card['key'] = key
        return {
            'title': _("Factory on one screen"),
            'period': _("Last %(days)s days · %(date)s", days=PERIOD_DAYS, date=today.strftime('%d.%m.%Y')),
            'company': company.name,
            'cards': [card for _key, card in cards],
            'by_key': dict(cards),
            'note': _("Margin: one weighted figure (margin ÷ revenue) on the dashboard and in the reports."),
        }


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    td_dash_paid = fields.Monetary(string='Paid', compute='_compute_td_dash_due')
    td_dash_due = fields.Monetary(string='Due', compute='_compute_td_dash_due')

    @api.depends('amount_total', 'invoice_ids.amount_residual', 'invoice_ids.state')
    def _compute_td_dash_due(self):
        for order in self:
            # the same paid amount as the payment control of the visit (td_mebli_install, F-22)
            paid = order._td_paid_amount()
            order.td_dash_paid = paid
            order.td_dash_due = max(0.0, order.amount_total - paid)
