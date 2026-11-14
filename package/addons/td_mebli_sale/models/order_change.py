from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

KINDS = [('change', 'Change'), ('reorder', 'Additional Order')]


class TdMebliOrderChange(models.Model):
    """A change of a confirmed order (S-18): the reason is entered, the price and the promised date before and after are
    copies of the standard fields of the order taken by the system when the change is opened and when it is closed."""
    _name = 'td.mebli.order.change'
    _description = 'Change of a Furniture Order'
    _order = 'order_id, version'

    order_id = fields.Many2one('sale.order', string='Order', required=True, ondelete='cascade', index=True)
    # AC-036 (tr/security.md §3): the company of the order and the global multi-company rule
    company_id = fields.Many2one(related='order_id.company_id', store=True, index=True, string='Company')
    version = fields.Integer(string='Version', required=True, readonly=True)
    # AC-119: after the parts are sent to cutting only an additional order (a new line / manufacturing order) is possible
    kind = fields.Selection(KINDS, string='Kind', required=True, default='change', readonly=True)
    reason = fields.Selection([('customer', 'Customer'), ('company', 'Company'), ('supplier', 'Supplier')],
                              string='Reason', required=True)
    note = fields.Char(string='What Changes', required=True)
    state = fields.Selection([('open', 'Being Changed'), ('done', 'Fixed'), ('signed', 'Signed by the Customer')],
                             string='Status', default='open', readonly=True)
    # AC-120 (box B, group_feature_change_sign): the customer signs the fixed change in the portal of the order
    td_sign_requested = fields.Boolean(string='Sent for Signature', readonly=True, copy=False)
    signature = fields.Image(string='Signature of the Customer', copy=False, attachment=True, max_width=1024,
                             max_height=1024)
    signed_by = fields.Char(string='Signed by', copy=False, readonly=True)
    signed_on = fields.Datetime(string='Signed on', copy=False, readonly=True)
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
            done = change.state in ('done', 'signed')
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

    def action_td_send_sign(self):
        """AC-120: the letter with the link to the portal of the order, where the customer signs the fixed change."""
        self.ensure_one()
        if not self.env.user.has_group('td_mebli_base.group_feature_change_sign'):
            raise AccessError(self.env._("Signing a change by the customer is not on in this database."))
        if self.state != 'done':
            raise UserError(self.env._("Only a fixed change can be sent for signature."))
        self.td_sign_requested = True
        order = self.order_id
        order._portal_ensure_token()
        template = self.env.ref('td_mebli_sale.mail_template_td_change_sign')
        return {
            'type': 'ir.actions.act_window', 'res_model': 'mail.compose.message', 'view_mode': 'form', 'target': 'new',
            'views': [(False, 'form')], 'name': self.env._("Send the Change for Signature"),
            'context': {'default_model': 'sale.order', 'default_res_ids': order.ids, 'default_template_id': template.id,
                        'default_composition_mode': 'comment', 'default_email_layout_xmlid': 'mail.mail_notification_light',
                        'td_change_id': self.id, 'mark_so_as_sent': False},
        }

    def _td_sign(self, name, signature):
        """The signature of the customer from the portal (the caller checks the access token of the order)."""
        self.ensure_one()
        if self.state != 'done' or not self.td_sign_requested:
            raise UserError(self.env._("This change is not waiting for the signature of the customer."))
        if not signature:
            raise UserError(self.env._("Signature is missing."))
        self.write({'signature': signature, 'signed_by': name, 'signed_on': fields.Datetime.now(), 'state': 'signed'})
        self.order_id.message_post(body=self.env._("Change %(version)s signed by the customer: %(name)s",
                                                   version=self.version, name=name or ''),
                                   subtype_xmlid='mail.mt_note')
        return True


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    td_change_ids = fields.One2many('td.mebli.order.change', 'order_id', string='Changes')
    td_change_open = fields.Boolean(string='Change Open', compute='_compute_td_change_open')

    @api.depends('td_change_ids.state')
    def _compute_td_change_open(self):
        for order in self:
            order.td_change_open = any(c.state == 'open' for c in order.td_change_ids)

    def _td_cut_version(self):
        """AC-119: the highest version of the order specifications already sent to cutting (0 — none sent):
        mrp.bom.td_cut_version of td_mebli_mrp, set when the parts go to cutting or to the distributor."""
        self.ensure_one()
        # sudo: read only — the cut version of the specifications for a salesperson without manufacturing rights
        return max(self.sudo().order_line.td_bom_id.mapped('td_cut_version') or [0])

    def action_td_open_change(self):
        self.ensure_one()
        cut = self._td_cut_version()
        return {'type': 'ir.actions.act_window', 'res_model': 'td.mebli.order.change.wizard', 'view_mode': 'form',
                'target': 'new', 'name': self.env._("Create a Change"),
                'context': {'default_order_id': self.id, 'default_kind': 'reorder' if cut else 'change'}}

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
    kind = fields.Selection(KINDS, string='Kind', required=True, default='change')
    cut_version = fields.Integer(string='Sent to Cutting, Version', compute='_compute_cut_version')

    @api.depends('order_id')
    def _compute_cut_version(self):
        for wizard in self:
            wizard.cut_version = wizard.order_id._td_cut_version() if wizard.order_id else 0

    def action_create(self):
        self.ensure_one()
        order = self.order_id
        if order.td_change_open:
            raise UserError(self.env._("The previous change of this order is not fixed yet."))
        cut = order._td_cut_version()
        if cut and self.kind != 'reorder':
            # AC-119 → the message of AC-052
            raise UserError(self.env._("The specification has been sent to cutting (version %s) — changes only by an "
                                       "additional order", cut))
        Change = self.env['td.mebli.order.change']
        amount, date = Change._td_snapshot(order)
        Change.create({'order_id': order.id, 'version': len(order.td_change_ids) + 2, 'reason': self.reason,
                       'note': self.note, 'kind': self.kind, 'amount_before': amount, 'date_before': date})
        return True
