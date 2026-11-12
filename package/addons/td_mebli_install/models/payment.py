from odoo import api, fields, models
from odoo.exceptions import UserError

PARAM_CONTROL = 'td_mebli_install.payment_control'  # «warn» (default) or «block»
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

    def _td_paid_amount(self):
        """Paid by the customer on the posted invoices of the order (standard account.move: amount_residual, payment_state).

        «In payment» counts as paid: the payment is registered, the bank reconciliation is the accountant's step."""
        self.ensure_one()
        paid = 0.0
        for move in self.sudo().invoice_ids.filtered(lambda m: m.state == 'posted'):
            amount = move.amount_total if move.payment_state in ('paid', 'in_payment') \
                else move.amount_total - move.amount_residual
            paid += -amount if move.move_type == 'out_refund' else amount
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

    @api.model
    def _td_payment_control(self):
        return self.env['ir.config_parameter'].sudo().get_param(PARAM_CONTROL, 'warn')

    def _compute_td_pay(self):
        control = self._td_payment_control()
        for order in self:
            # sudo: read only — the crew and the salesperson see the figures, the invoices stay with Accounting
            due = order.sudo()._td_due_before_install() if order.state == 'sale' else 0.0
            paid = order.sudo()._td_paid_amount() if order.id else 0.0
            order.td_pay_before_install = due
            order.td_pay_received = paid
            order.td_pay_missing = max(0.0, due - paid) if due - paid >= ROUNDING else 0.0
            order.td_pay_ok = not order.td_pay_missing
            order.td_pay_control = control

    def _td_check_payment(self, action):
        """Before the crew starts or the customer signs: warn (default) or block by the parameter of the company."""
        if self._td_payment_control() != 'block':
            return True
        for order in self.sudo().filtered(lambda o: o.state == 'sale' and not o.td_pay_ok):
            raise UserError(self.env._(
                "%(action)s: the order %(order)s is not paid before the installation, %(missing)s missing. "
                "The payment control blocks it (Project settings, «Payment before installation»).",
                action=action, order=order.name,
                missing=f"{order.td_pay_missing:,.2f} {order.currency_id.symbol}".replace(',', ' ')))
        return True


class ProjectTask(models.Model):
    _inherit = 'project.task'

    td_pay_ok = fields.Boolean(related='sale_order_id.td_pay_ok', string='Paid before Installation')
    td_pay_missing = fields.Monetary(related='sale_order_id.td_pay_missing', currency_field='td_order_currency_id')
    td_pay_control = fields.Selection(related='sale_order_id.td_pay_control')
    td_order_currency_id = fields.Many2one(related='sale_order_id.currency_id', string='Order Currency')

    def action_td_start_install(self):
        """«Start the installation» on the visit: the payment control, the task in progress, the act of the visit."""
        self.ensure_one()
        self.sale_order_id._td_check_payment(self.env._("Start the installation"))
        if self.state not in ('1_done', '1_canceled'):
            self.state = '01_in_progress'
        if not self.td_act_ids:
            final = self.env['td.mebli.install.act'].sudo().search_count(
                [('order_id', '=', self.sale_order_id.id), ('kind', '=', 'final')], limit=1)
            self.env['td.mebli.install.act'].create({'task_id': self.id, 'kind': 'stage' if final else 'final'})
        return self.action_td_view_acts()


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    td_mebli_payment_control = fields.Selection(
        [('warn', 'Warn'), ('block', 'Block')], string='Payment before Installation', default='warn',
        config_parameter=PARAM_CONTROL,
        help="Warn: the visit, the act and the order show that the payment due before the installation is missing. "
             "Block: besides, «Start the installation» and «Sign the act» are refused until it is paid.")
