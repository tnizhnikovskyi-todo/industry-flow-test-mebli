from odoo import api, fields, models
from odoo.exceptions import UserError


class TdMebliOrderChange(models.Model):
    """A change of a confirmed order (S-18): the reason is entered, the price and the promised date before and after are
    copies of the standard fields of the order taken by the system when the change is opened and when it is closed."""
    _name = 'td.mebli.order.change'
    _description = 'Change of a Furniture Order'
    _order = 'order_id, version'

    order_id = fields.Many2one('sale.order', string='Order', required=True, ondelete='cascade', index=True)
    version = fields.Integer(string='Version', required=True, readonly=True)
    reason = fields.Selection([('customer', 'Customer'), ('company', 'Company'), ('supplier', 'Supplier')],
                              string='Reason', required=True)
    note = fields.Char(string='What Changes', required=True)
    state = fields.Selection([('open', 'Being Changed'), ('done', 'Fixed')], string='Status', default='open', readonly=True)
    currency_id = fields.Many2one(related='order_id.currency_id')
    amount_before = fields.Monetary(string='Price Before', readonly=True)
    amount_after = fields.Monetary(string='Price After', readonly=True)
    date_before = fields.Date(string='Promised Before', readonly=True)
    date_after = fields.Date(string='Promised After', readonly=True)
    shift_days = fields.Integer(string='Shift, days', compute='_compute_shift', store=True)
    amount_delta = fields.Monetary(string='Price Change', compute='_compute_shift', store=True)

    _version_unique = models.Constraint('UNIQUE(order_id, version)', 'The version of a change is unique in an order.')

    @api.depends('date_before', 'date_after', 'amount_before', 'amount_after', 'state')
    def _compute_shift(self):
        for change in self:
            done = change.state == 'done'
            change.shift_days = (change.date_after - change.date_before).days \
                if done and change.date_before and change.date_after else 0
            change.amount_delta = change.amount_after - change.amount_before if done else 0.0

    @api.model
    def _td_snapshot(self, order):
        return order.amount_untaxed, fields.Date.context_today(self, order.commitment_date) if order.commitment_date else False

    def action_fix(self):
        """Closes the change: the price and the promised date after the change are read from the order."""
        for change in self.filtered(lambda c: c.state == 'open'):
            amount, date = self._td_snapshot(change.order_id)
            change.write({'state': 'done', 'amount_after': amount, 'date_after': date})
            change.order_id.message_post(body=self.env._(
                "Change %(version)s fixed (%(reason)s): %(note)s", version=change.version,
                reason=dict(self._fields['reason']._description_selection(self.env))[change.reason], note=change.note))
        return True


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    td_change_ids = fields.One2many('td.mebli.order.change', 'order_id', string='Changes')
    td_change_open = fields.Boolean(string='Change Open', compute='_compute_td_change_open')

    @api.depends('td_change_ids.state')
    def _compute_td_change_open(self):
        for order in self:
            order.td_change_open = any(c.state == 'open' for c in order.td_change_ids)

    def action_td_open_change(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'res_model': 'td.mebli.order.change.wizard', 'view_mode': 'form',
                'target': 'new', 'name': self.env._("Create a Change"), 'context': {'default_order_id': self.id}}

    def action_td_fix_change(self):
        self.td_change_ids.action_fix()
        return True


class TdMebliOrderChangeWizard(models.TransientModel):
    _name = 'td.mebli.order.change.wizard'
    _description = 'Create a Change of an Order'

    order_id = fields.Many2one('sale.order', required=True)
    reason = fields.Selection([('customer', 'Customer'), ('company', 'Company'), ('supplier', 'Supplier')],
                              string='Reason', required=True, default='customer')
    note = fields.Char(string='What Changes', required=True)

    def action_create(self):
        self.ensure_one()
        order = self.order_id
        if order.td_change_open:
            raise UserError(self.env._("The previous change of this order is not fixed yet."))
        Change = self.env['td.mebli.order.change']
        amount, date = Change._td_snapshot(order)
        Change.create({'order_id': order.id, 'version': len(order.td_change_ids) + 2, 'reason': self.reason,
                       'note': self.note, 'amount_before': amount, 'date_before': date})
        return True
