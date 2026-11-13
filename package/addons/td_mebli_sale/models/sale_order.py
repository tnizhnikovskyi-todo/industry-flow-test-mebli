from datetime import timedelta

from odoo import api, fields, models
from odoo.fields import Domain
from odoo.exceptions import UserError

from .sale_order_line import MARGIN_GROUPS


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    td_launch_date = fields.Datetime(string='Production Started', compute='_compute_td_launch')
    td_hours_to_launch = fields.Float(string='To Launch, h', compute='_compute_td_launch', digits=(16, 1))
    td_production_count = fields.Integer(string='Production', compute='_compute_td_production_count')
    td_stage = fields.Selection(
        [('quote', 'Quotation'), ('sent', 'Sent to customer'), ('confirmed', 'Waiting for launch'),
         ('progress', 'In production'), ('done', 'Made')],
        string='Order Stage', compute='_compute_td_stage', inverse='_inverse_td_stage', store=True, readonly=False,
        copy=False, group_expand='_read_group_td_stage')  # copy=False: «Duplicate» recomputes, not the inverse
    # AC-067: the last time the stage of the board changed (kept by the computation of the stage, not entered)
    td_stage_date = fields.Datetime(string='Stage Changed', readonly=True, copy=False, index=True,
                                    default=fields.Datetime.now)
    td_is_stuck = fields.Boolean(string='Stuck', compute='_compute_td_is_stuck', search='_search_td_is_stuck',
                                 help="A confirmed order whose stage did not change for longer than «Stuck orders, days "
                                      "without a move» of its company (VP-10).")
    # AC-018: the standard margin of sale_margin — the same groups as the planned cost
    margin = fields.Monetary(groups=MARGIN_GROUPS)
    margin_percent = fields.Float(groups=MARGIN_GROUPS)
    td_image = fields.Image(string='Product Image', compute='_compute_td_image', max_width=256, max_height=256)
    # position 6: the visual of the designer goes into the standard quotation PDF (sale.report_saleorder_document)
    td_design_image = fields.Image(string='Design Visual', max_width=1600, max_height=1600, copy=False,
                                   help="The visual of the project from the designer: printed in the quotation under the "
                                        "order details.")

    @api.model
    def _read_group_td_stage(self, values, domain):
        """All stages of the board are shown in order, also the empty ones."""
        return [key for key, _label in self._fields['td_stage'].selection]

    @api.depends('state', 'stock_reference_ids.production_ids.state')
    def _compute_td_stage(self):
        for order in self:
            # sudo: the stage is shown to a salesperson who has no right to read every manufacturing order
            states = order.sudo().mrp_production_ids.mapped('state')
            if order.state in ('draft', 'cancel'):
                order.td_stage = 'quote'
            elif order.state == 'sent':
                order.td_stage = 'sent'
            elif states and all(state == 'done' for state in states):
                order.td_stage = 'done'
            elif any(state in ('progress', 'to_close', 'done') for state in states):
                order.td_stage = 'progress'
            else:
                order.td_stage = 'confirmed'

    def _inverse_td_stage(self):
        """Dragging a card on the board: only «Waiting for launch» -> «In production» is allowed and it really starts the
        work (the first work order of each manufacturing order); any other move is refused, the stage is derived from the work.

        Only a manufacturing user may start the work, with his own rights (no sudo): a salesperson gets an error and the
        button «Start» stays in the manufacturing order."""
        # AC-064: the text of SPEC
        message = self.env._("The stage is computed from the documents; only the production manager launches production")
        if not (self.env.su or self.env.user.has_group('mrp.group_mrp_user')):
            raise UserError(message)
        for order in self:
            if order.td_stage != 'progress':
                raise UserError(self.env._("The stage follows the production: only moving a waiting order to «In production» is possible."))
            productions = order.mrp_production_ids.filtered(lambda p: p.state == 'confirmed')
            if not productions:
                raise UserError(self.env._("This order has nothing to start: it is not waiting for launch."))
            for production in productions:
                if not production.workorder_ids:
                    production.button_plan()
                first = production.workorder_ids.filtered(lambda w: w.state in ('ready', 'blocked'))[:1]
                if first:
                    first.button_start()

    def _write_multi(self, vals_list):
        """AC-067: «Stage Changed» moves when the stored stage really changes (the stage is computed, so the low-level
        write of the computed value is the one place that sees the old and the new stage after every override)."""
        if any('td_stage' in vals for vals in vals_list):
            self.env.cr.execute("SELECT id, td_stage FROM sale_order WHERE id IN %s", [tuple(self.ids)])
            before = dict(self.env.cr.fetchall())
            now = fields.Datetime.now()
            vals_list = [dict(vals, td_stage_date=now)
                         if 'td_stage' in vals and 'td_stage_date' not in vals and before.get(order.id) != vals['td_stage']
                         else vals for order, vals in zip(self, vals_list)]
            super()._write_multi(vals_list)
            self.invalidate_recordset(['td_stage_date'])
            return
        super()._write_multi(vals_list)

    @api.depends_context('uid')
    def _compute_td_is_stuck(self):
        stuck = self.search([('id', 'in', [o.id for o in self if isinstance(o.id, int)]), ('td_is_stuck', '=', True)])
        for order in self:
            order.td_is_stuck = order in stuck

    @api.model
    def _td_stuck_domain(self):
        """AC-067: per company of the reader, the number of days of the company (VP-10) — read at the time of the
        search, so a change of the parameter applies at once."""
        now = fields.Datetime.now()
        stages = [key for key, _label in self._fields['td_stage'].selection if key not in ('quote', 'sent', 'closed')]
        by_company = Domain.OR(
            Domain('company_id', '=', company.id)
            & Domain('td_stage_date', '<', now - timedelta(days=company.td_stuck_days or 5))
            for company in self.env.companies)
        return Domain('state', '=', 'sale') & Domain('td_stage', 'in', stages) & by_company

    def _search_td_is_stuck(self, operator, value):
        if operator != 'in':
            return NotImplemented
        domain = Domain(self._td_stuck_domain())
        if True in value and False in value:
            return Domain.TRUE
        return domain if True in value else ~domain

    def _compute_td_image(self):
        for order in self:
            order.td_image = order.order_line.filtered(lambda line: line.product_id and not line.display_type)[:1].product_id.image_256

    @api.depends('stock_reference_ids.production_ids')
    def _compute_td_production_count(self):
        for order in self:
            # sudo: mrp_production_ids is limited to the manufacturing group, the salesperson sees only the count
            order.td_production_count = len(order.sudo().mrp_production_ids)

    def action_confirm(self):
        """The manufacturing orders are created on confirmation: say so in the order chatter."""
        result = super().action_confirm()
        for order in self:
            # the salesperson may read the manufacturing orders (access rule), but a sudo is kept for the names:
            # the order must not fail on confirmation if some rule hides a manufacturing order
            names = order.sudo().mrp_production_ids.mapped('name')
            if names:
                order.message_post(body=self.env._("Manufacturing order created: %s.", ', '.join(names)),
                                   subtype_xmlid='mail.mt_note')
        return result

    def action_td_view_production(self):
        """Open the manufacturing orders of the order (the salesperson has read access to them by an access rule)."""
        self.ensure_one()
        productions = self.sudo().mrp_production_ids
        action = {'type': 'ir.actions.act_window', 'res_model': 'mrp.production'}
        if len(productions) == 1:
            return dict(action, view_mode='form', res_id=productions.id)
        return dict(action, name=self.env._("Manufacturing orders of %s", self.name), view_mode='list,form',
                    domain=[('id', 'in', productions.ids)])

    @api.depends('date_order', 'state')  # the work orders are reached through a non-stored field: recomputed on every read
    def _compute_td_launch(self):
        """Hours from the order date to the first time actually booked on a work order of its manufacturing orders.

        A confirmed order that is not launched yet shows how long it has been waiting so far."""
        now = fields.Datetime.now()
        for order in self:
            # sudo: a salesperson has no rights on work orders, but may see how long the order waited
            starts = order.sudo().mrp_production_ids.workorder_ids.time_ids.mapped('date_start')
            order.td_launch_date = min(starts) if starts else False
            if starts and order.date_order:
                order.td_hours_to_launch = max((min(starts) - order.date_order).total_seconds() / 3600.0, 0.0)
            elif order.state == 'sale' and order.date_order:
                order.td_hours_to_launch = max((now - order.date_order).total_seconds() / 3600.0, 0.0)
            else:
                order.td_hours_to_launch = 0.0


class SaleReport(models.Model):
    _inherit = 'sale.report'

    # AC-018: the margin measure of the sales analysis — the same groups as the margin of the order
    margin = fields.Float(groups=MARGIN_GROUPS)
