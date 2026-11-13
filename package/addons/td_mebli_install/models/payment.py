from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Domain

ROUNDING = 0.5  # UAH: an amount due below it is paid (rounding of the bank)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    td_act_ids = fields.One2many('td.mebli.install.act', 'order_id', string='Installation Acts')
    td_pay_before_install = fields.Monetary(
        string='Due before Installation', compute='_compute_td_pay',
        help="Read only: the lines of the payment terms that are not «After the act» (the whole amount when the terms "
             "have no milestones).")
    td_pay_received = fields.Monetary(
        string='Received', compute='_compute_td_pay',
        help="Read only: what the customer has paid on the posted invoices of the order (the down payments included), "
             "less the credit notes.")
    td_pay_missing = fields.Monetary(string='Missing before Installation', compute='_compute_td_pay')
    td_pay_ok = fields.Boolean(string='Paid before Installation', compute='_compute_td_pay')
    td_pay_control = fields.Selection([('warn', 'Warn'), ('block', 'Block')], compute='_compute_td_pay')
    # AC-021: the payment is in the bank, the exchange with BAS has not brought it yet — the finance marks it by hand
    td_pay_mark_ids = fields.One2many('td.mebli.pay.mark', 'order_id', string='Manual Payment Marks')

    def _td_paid_amount(self):
        """Paid by the customer on the posted invoices of the order (standard account.move: amount_residual, payment_state).

        «In payment» counts as paid: the payment is registered, the bank reconciliation is the accountant's step."""
        self.ensure_one()
        paid = 0.0
        for move in self.sudo().invoice_ids.filtered(lambda m: m.state == 'posted'):
            amount = move.amount_total if move.payment_state in ('paid', 'in_payment') \
                else move.amount_total - move.amount_residual
            paid += -amount if move.move_type == 'out_refund' else amount
        # AC-021: the manual marks of the finance (not cancelled) count as received
        paid += sum(self.sudo().td_pay_mark_ids.filtered(lambda mark: not mark.cancelled).mapped('amount'))
        return paid

    def _td_due_before_install(self):
        """The share of the order amount the payment terms ask before the installation (not «After the act»)."""
        self.ensure_one()
        lines = self.payment_term_id.line_ids
        total = self.amount_total
        if not lines:
            return total
        due = 0.0
        for line in lines.filtered(lambda line: line.td_milestone != 'act'):
            due += total * line.value_amount / 100.0 if line.value == 'percent' else line.value_amount
        return min(total, due)

    def _td_payment_control(self):
        """VP-06: the field of the company of the order (td_mebli_base), «warn» when it is empty."""
        company = self[:1].company_id or self.env.company
        return company.sudo().td_payment_control or 'warn'

    def _compute_td_pay(self):
        for order in self:
            control = order._td_payment_control()
            # sudo: read only — the crew and the salesperson see the figures, the invoices stay with Accounting
            due = order.sudo()._td_due_before_install() if order.state == 'sale' else 0.0
            paid = order.sudo()._td_paid_amount() if order.id else 0.0
            order.td_pay_before_install = due
            order.td_pay_received = paid
            order.td_pay_missing = max(0.0, due - paid) if due - paid >= ROUNDING else 0.0
            order.td_pay_ok = not order.td_pay_missing
            order.td_pay_control = control

    def _td_missing_text(self):
        self.ensure_one()
        return f"{self.td_pay_missing:,.2f} {self.currency_id.symbol}".replace(',', ' ')

    def _td_check_payment(self, action):
        """AC-020, before the crew starts or the customer signs (VP-06 of the company of the order).

        Block: the error of SPEC, nothing changes. Warn (default): the action goes on, the order chatter keeps the
        warning; the banner is on the order, the visit and the act."""
        for order in self.sudo().filtered(lambda o: o.state == 'sale' and not o.td_pay_ok):
            missing = order._td_missing_text()
            if order._td_payment_control() == 'block':
                raise UserError(self.env._(
                    "Installation blocked: the payment of %(missing)s is not received. Contact the manager",
                    missing=missing))
            order.message_post(body=Markup('%s<br/>%s') % (
                self.env._("Payment before installation not received: %(missing)s", missing=missing), action))
        return True


class ProjectTask(models.Model):
    _inherit = 'project.task'

    td_pay_ok = fields.Boolean(related='sale_order_id.td_pay_ok', string='Paid before Installation')
    td_pay_missing = fields.Monetary(related='sale_order_id.td_pay_missing', currency_field='td_order_currency_id')
    td_pay_control = fields.Selection(related='sale_order_id.td_pay_control')
    td_order_currency_id = fields.Many2one(related='sale_order_id.currency_id', string='Order Currency')

    td_visit_kind = fields.Selection(
        [('install', 'Installation'), ('service', 'Service')], string='Visit Kind', default='install',
        help="Service: a visit by a claim (no installation act, no payment control).")

    def action_td_start_install(self):
        """«Start the installation» on the visit: the payment control, the task in progress, the act of the visit."""
        self.ensure_one()
        if self.td_visit_kind == 'service':  # a visit by a claim: no payment control, no installation act
            if self.state not in ('1_done', '1_canceled'):
                self.state = '01_in_progress'
            return True
        self.sale_order_id._td_check_payment(self.env._("Start the installation"))
        if self.state not in ('1_done', '1_canceled'):
            self.state = '01_in_progress'
        if not self.td_act_ids:
            final = self.env['td.mebli.install.act'].sudo().search_count(
                [('order_id', '=', self.sale_order_id.id), ('kind', '=', 'final')], limit=1)
            self.env['td.mebli.install.act'].create({'task_id': self.id, 'kind': 'stage' if final else 'final'})
        return self.action_td_view_acts()


class TdMebliPayMark(models.Model):
    """AC-021 (AI-15): a manual mark «Payment confirmed by hand» of the finance or the director.

    The payment is in the bank, the exchange with BAS has not brought it yet: the payment control of the order counts
    the mark as received. Cancelled (not deleted) when the payment comes by the exchange (AC-042, td_mebli_bas)."""
    _name = 'td.mebli.pay.mark'
    _description = 'Manual Payment Mark'
    _order = 'id desc'

    order_id = fields.Many2one('sale.order', string='Order', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='order_id.company_id', store=True, string='Company', index=True)
    currency_id = fields.Many2one(related='order_id.currency_id', string='Currency')
    amount = fields.Monetary(string='Amount', required=True)
    reason = fields.Char(string='Reason')
    user_id = fields.Many2one('res.users', string='Marked by', default=lambda self: self.env.user, readonly=True)
    date = fields.Datetime(string='Marked on', default=fields.Datetime.now, readonly=True)
    cancelled = fields.Boolean(string='Cancelled', help="The payment came by the exchange: the mark no longer counts.")

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        order = self.env['sale.order'].browse(values.get('order_id') or self.env.context.get('default_order_id'))
        if 'amount' in fields_list and order.exists() and not values.get('amount'):
            values['amount'] = order.td_pay_missing
        return values

    @api.constrains('reason', 'amount')
    def _check_td_mark(self):
        for mark in self:
            if not (mark.reason or '').strip():
                raise ValidationError(self.env._("Specify the reason of the manual payment mark"))
            if mark.amount <= 0:
                raise ValidationError(self.env._("The amount of the manual payment mark must be positive."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:  # the error of SPEC before the database constraint
            if not (vals.get('reason') or '').strip():
                raise ValidationError(self.env._("Specify the reason of the manual payment mark"))
        marks = super().create(vals_list)
        for mark in marks:
            mark.order_id.sudo().message_post(body=self.env._(
                "Payment confirmed by hand: %(amount)s %(currency)s, %(user)s, %(date)s. Reason: %(reason)s",
                amount=f"{mark.amount:,.2f}".replace(',', ' '), currency=mark.currency_id.symbol or '',
                user=mark.user_id.name, date=fields.Datetime.to_string(mark.date), reason=mark.reason))
        return marks

    def write(self, vals):
        """Review A-11: the amount of a mark is fixed once it is saved (a new mark instead); every change of a mark
        is written to the chatter of the order — the cancellation and any other field."""
        if 'amount' in vals and not self.env.su and any(
                mark.currency_id.compare_amounts(mark.amount, vals['amount']) for mark in self):
            raise UserError(self.env._("The amount of a manual payment mark is not changed: cancel it and add a new one."))
        logged = [name for name in vals if name in self._fields and name not in ('cancelled', 'write_date', 'write_uid')]
        before = {mark.id: {name: mark[name] for name in logged} for mark in self}
        res = super().write(vals)
        for mark in self:
            if vals.get('cancelled'):
                mark.order_id.sudo().message_post(body=self.env._(
                    "Manual payment mark cancelled: %(amount)s, %(user)s.",
                    amount=f"{mark.amount:,.2f}".replace(',', ' '), user=self.env.user.name))
            elif 'cancelled' in vals:
                mark.order_id.sudo().message_post(body=self.env._(
                    "Manual payment mark restored: %(amount)s, %(user)s.",
                    amount=f"{mark.amount:,.2f}".replace(',', ' '), user=self.env.user.name))
            changes = [f"{mark._fields[name].get_description(self.env)['string']}: "
                       f"{mark._td_log_value(name, before[mark.id][name])} → {mark._td_log_value(name, mark[name])}"
                       for name in logged if before[mark.id][name] != mark[name]]
            if changes:
                mark.order_id.sudo().message_post(body=self.env._(
                    "Manual payment mark changed by %(user)s: %(changes)s",
                    user=self.env.user.name, changes='; '.join(changes)))
        return res

    def _td_log_value(self, name, value):
        if isinstance(value, models.BaseModel):
            return value.display_name or '—'
        if self._fields[name].type == 'monetary':
            return f"{value:,.2f}".replace(',', ' ')
        return '—' if value in (False, None, '') else str(value)

    def action_td_save(self):
        """The button of the dialog: the record is saved by the client before the call."""
        return {'type': 'ir.actions.act_window_close'}


class SaleOrderPayMark(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _td_forecast_open_domain(self):
        """Review A-11: an order with a signed final act is finished — the forecast cron skips it."""
        return Domain(super()._td_forecast_open_domain()) & Domain(
            'td_act_ids', 'not any', [('kind', '=', 'final'), ('state', '=', 'signed')])

    def _td_cancel_pay_marks(self, amount=None):
        """AC-042: a payment of the order arrived by the exchange with BAS — the manual marks that stood in for it are
        cancelled (kept, not deleted). `amount` — the amount of the payment: only the marks of the same amount are
        cancelled (tr/integrations.md §1.3 п.3); None — all the open marks. Called from the BAS hook
        `_td_after_bas_payment` (td_mebli_bas)."""
        marks = self.sudo().td_pay_mark_ids.filtered(
            lambda mark: not mark.cancelled and (amount is None or not mark.currency_id.compare_amounts(mark.amount, amount)))
        if marks:
            marks.write({'cancelled': True})
        return marks

    def action_td_pay_mark(self):
        """«Payment confirmed by hand» (finance, director): the dialog of a new mark with the reason."""
        self.ensure_one()
        self.env['td.mebli.pay.mark'].check_access('create')
        return {
            'type': 'ir.actions.act_window', 'name': self.env._("Payment Confirmed by Hand"),
            'res_model': 'td.mebli.pay.mark', 'view_mode': 'form', 'target': 'new',
            'views': [(self.env.ref('td_mebli_install.td_mebli_pay_mark_view_form').id, 'form')],
            'context': {'default_order_id': self.id},
        }
