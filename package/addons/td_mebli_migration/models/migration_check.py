from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero

METRICS = [('prepayment', 'Prepayments of Open Orders'), ('open_orders', 'Open Orders'), ('stock', 'Stock of a Product')]


class TdMebliMigrationCheck(models.Model):
    """Reconciliation of the migration (AC-089, AC-090; tr/migration.md §3): the values of the source against Odoo."""
    _name = 'td.mebli.migration.check'
    _description = 'Migration Reconciliation'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reconciliation', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    date = fields.Date(string='Date of the Data', required=True, default=fields.Date.context_today,
                       help="The date of the stock and of the payments in the source (one date, box A).")
    state = fields.Selection([('draft', 'Draft'), ('diff', 'Difference'), ('reconciled', 'Reconciled'),
                              ('explained', 'Explained')], string='Status', default='draft', required=True,
                             readonly=True, tracking=True)
    line_ids = fields.One2many('td.mebli.migration.check.line', 'check_id', string='Lines', copy=True)
    has_diff = fields.Boolean(string='Has a Difference', compute='_compute_has_diff')
    explanation = fields.Text(string='Explanation', tracking=True,
                              help="Why the difference is accepted; signed by a manager (button «Sign the Explanation»).")
    explained_by = fields.Many2one('res.users', string='Signed by', readonly=True, copy=False)
    explained_on = fields.Datetime(string='Signed on', readonly=True, copy=False)

    @api.depends('line_ids.diff')
    def _compute_has_diff(self):
        for check in self:
            check.has_diff = any(not float_is_zero(line.diff, precision_digits=2) for line in check.line_ids)

    @api.constrains('state', 'line_ids', 'explained_by')
    def _check_reconciled(self):
        for check in self:
            if check.state == 'reconciled' and check.has_diff:
                raise ValidationError(self.env._("«Reconciled» only with a zero difference."))
            if check.state == 'explained' and not (check.explanation and check.explained_by):
                raise ValidationError(self.env._("«Explained» only with an explanation signed by a manager."))

    # ------------------------------------------------------------------ Odoo side
    def _td_open_orders(self):
        """Open orders of the start (box A: confirmed, not delivered in full)."""
        self.ensure_one()
        orders = self.env['sale.order'].search([('company_id', '=', self.company_id.id), ('state', '=', 'sale')])
        return orders.filtered(lambda o: any(
            line.qty_delivered < line.product_uom_qty for line in o.order_line
            if not line.display_type and not line.is_downpayment))

    @api.model
    def _td_prepayment(self, order):
        """Paid on the posted invoices of the order (standard: amount_total − amount_residual; refunds negative)."""
        paid = 0.0
        # sudo: read only: the posted invoices of the order for the reconciliation of the finance
        for move in order.sudo().invoice_ids.filtered(lambda m: m.state == 'posted'):
            amount = move.amount_total - move.amount_residual
            paid += -amount if move.move_type == 'out_refund' else amount
        return paid

    def action_td_compute(self):
        """Fills the values of Odoo, the differences and the records-causes; the status follows the difference."""
        for check in self:
            if check.state in ('reconciled', 'explained'):
                raise UserError(self.env._("The reconciliation %s is closed.", check.name))
            orders = check._td_open_orders()
            prepayments = {order: check._td_prepayment(order) for order in orders}
            for line in check.line_ids:
                causes = self.env['sale.order']
                if line.metric == 'prepayment':
                    if line.order_ref:
                        matched = orders.filtered(lambda o: line.order_ref in (o.name, o.client_order_ref, o.origin))
                        value = sum(prepayments[o] for o in matched)
                        causes = matched
                    else:
                        value = sum(prepayments.values())
                        causes = orders.filtered(lambda o: not float_is_zero(prepayments[o], precision_digits=2))
                elif line.metric == 'open_orders':
                    value = len(orders)
                    causes = orders
                else:
                    value = line.product_id.with_company(check.company_id).with_context(
                        to_date=fields.Datetime.end_of(fields.Datetime.to_datetime(check.date), 'day')).qty_available
                line.write({'value_odoo': value,
                            'cause_order_ids': [(6, 0, causes.ids if not float_is_zero(value - line.value_source,
                                                                                       precision_digits=2) else [])]})
            # sudo: the status follows the computed difference only; the finance computes, but does not write the status
            # itself (CHECKS.md No. 29: «Explained» and the status are guarded in write)
            check.sudo().state = 'diff' if check.has_diff else 'reconciled'
        return True

    def _td_check_manager(self, message):
        if not (self.env.su or self.env.user.has_group('sales_team.group_sale_manager')):
            raise AccessError(message)

    @api.model_create_multi
    def create(self, vals_list):
        # CHECKS.md No. 29: a reconciliation is created as a draft; «Explained» with a signature only by a manager
        for vals in vals_list:
            if vals.get('state', 'draft') != 'draft' or vals.get('explained_by') or vals.get('explained_on'):
                self._td_check_manager(self.env._("Only a manager signs the explanation of a difference."))
        return super().create(vals_list)

    def write(self, vals):
        # the signature of the explanation is written by «Sign the Explanation» / «Reset» only (a manager), not by RPC
        if {'explained_by', 'explained_on'} & set(vals):
            self._td_check_manager(self.env._("Only a manager signs the explanation of a difference."))
        # CHECKS.md No. 29: the status is set by «Compute» (the difference), «Sign the Explanation» and «Reset» only; the
        # finance writes the explanation of an open reconciliation, not of a signed or reconciled one
        if 'state' in vals:
            self._td_check_manager(self.env._("Only a manager changes the status of a reconciliation."))
        if 'explanation' in vals and any(check.state in ('reconciled', 'explained') for check in self):
            self._td_check_manager(self.env._("Only a manager changes the explanation of a closed reconciliation."))
        return super().write(vals)

    def action_td_sign_explanation(self):
        """«Sign the Explanation» (AC-090): a manager accepts the difference with a written reason."""
        if not self.env.user.has_group('sales_team.group_sale_manager'):
            raise AccessError(self.env._("Only a manager signs the explanation of a difference."))
        for check in self:
            if check.state != 'diff':
                raise UserError(self.env._("Only a reconciliation with a difference is explained."))
            if not (check.explanation or '').strip():
                raise UserError(self.env._("Write the explanation of the difference first."))
            check.write({'explained_by': self.env.user.id, 'explained_on': fields.Datetime.now(), 'state': 'explained'})
        return True

    def action_td_reset(self):
        # A-14 security 6: the signed explanation (AC-090) is reset by a manager only, checked on the server
        self._td_check_manager(self.env._("Only a manager resets a reconciliation."))
        self.write({'state': 'draft', 'explained_by': False, 'explained_on': False})
        return True


class TdMebliMigrationCheckLine(models.Model):
    _name = 'td.mebli.migration.check.line'
    _description = 'Migration Reconciliation Line'
    _order = 'check_id, sequence, id'

    check_id = fields.Many2one('td.mebli.migration.check', string='Reconciliation', required=True, ondelete='cascade',
                               index=True)
    sequence = fields.Integer(default=10)
    metric = fields.Selection(METRICS, string='Metric', required=True)
    order_ref = fields.Char(string='Order in the Source',
                            help="Prepayment of one order: its number in Odoo, the customer reference or the source "
                                 "document. Empty — all open orders.")
    product_id = fields.Many2one('product.product', string='Product')
    value_source = fields.Float(string='Source', digits=(16, 2))
    value_odoo = fields.Float(string='Odoo', digits=(16, 2), readonly=True)
    diff = fields.Float(string='Difference', digits=(16, 2), compute='_compute_diff', store=True)
    cause_order_ids = fields.Many2many('sale.order', string='Records to Check', readonly=True,
                                       help="Orders behind a difference: open orders with a prepayment (or the order "
                                            "of the line).")
    note = fields.Char(string='Note')

    def _td_check_open(self):
        # A-14 pr-review m3: a closed reconciliation (reconciled / explained) is not changed line by line — «Reset» first
        if not self.env.su and any(line.check_id.state in ('reconciled', 'explained') for line in self):
            raise UserError(self.env._("The reconciliation is closed: reset it first."))

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._td_check_open()
        return lines

    def write(self, vals):
        self._td_check_open()
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_closed(self):
        self._td_check_open()

    @api.depends('value_source', 'value_odoo')
    def _compute_diff(self):
        for line in self:
            line.diff = line.value_odoo - line.value_source

    @api.constrains('metric', 'product_id')
    def _check_product(self):
        for line in self:
            if line.metric == 'stock' and not line.product_id:
                raise ValidationError(self.env._("The stock line needs a product."))
