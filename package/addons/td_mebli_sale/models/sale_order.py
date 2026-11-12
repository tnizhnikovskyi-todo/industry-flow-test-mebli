from odoo import api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    td_launch_date = fields.Datetime(string='Production Started', compute='_compute_td_launch')
    td_hours_to_launch = fields.Float(string='To Launch, h', compute='_compute_td_launch', digits=(16, 1))
    td_production_count = fields.Integer(string='Production', compute='_compute_td_production_count')
    td_stage = fields.Selection(
        [('quote', 'Quotation'), ('sent', 'Sent to customer'), ('confirmed', 'Waiting for launch'),
         ('progress', 'In production'), ('done', 'Made')],
        string='Order Stage', compute='_compute_td_stage', inverse='_inverse_td_stage', store=True, readonly=False,
        group_expand='_read_group_td_stage')
    td_image = fields.Image(string='Product Image', compute='_compute_td_image', max_width=256, max_height=256)

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
        if not (self.env.su or self.env.user.has_group('mrp.group_mrp_user')):
            raise UserError(self.env._("Only a manufacturing user can start the production of an order."))
        for order in self:
            if order.td_stage != 'progress':
                raise UserError(self.env._("The stage follows the production: only moving a waiting order to «In production» is possible."))
            productions = order.mrp_production_ids.filtered(lambda p: p.state == 'confirmed')
            if not productions:
                raise UserError(self.env._("This order has nothing to start: it is not waiting for launch."))
            for production in productions:
                if not production.workorder_ids:
                    production.button_plan()
                first = production.workorder_ids.filtered(lambda w: w.state in ('ready', 'waiting', 'pending'))[:1]
                if first:
                    first.button_start()

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
