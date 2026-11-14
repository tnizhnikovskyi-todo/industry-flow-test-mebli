from markupsafe import Markup

from odoo import api, fields, models
from odoo.tools import format_amount
from odoo.exceptions import UserError


class AccountPaymentTermLine(models.Model):
    """F-22: the payment schedule of the order is the standard payment terms (several lines: 50 % now, 40 % ..., 10 % ...).

    The standard line knows only «how much» and «after how many days»; the furniture factory pays by the event of the
    order (confirmation, installation, act). The milestone is a new piece of data on the standard line (there is no such
    field in the standard), it only tells which lines have to be paid before the crew goes to the customer."""
    _inherit = 'account.payment.term.line'

    td_milestone = fields.Selection(
        [('order', 'Prepayment'), ('install', 'Before installation'), ('act', 'After the act')],
        string='Furniture Milestone',
        help="The event of the order this line is paid by. The lines «Prepayment» and «Before installation» have to be "
             "paid before the installation (the visit of the crew); «After the act» is paid after the signed act. "
             "Payment terms without milestones: the whole amount is due before the installation.")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # AC-019 (D-05, A-11-7): the amounts of the milestones are seen in the form of the order, not only in the contract
    td_pay_has_milestones = fields.Boolean(string='Payment by Milestones', compute='_compute_td_pay_schedule')
    td_pay_schedule_html = fields.Html(string='Payment Schedule', compute='_compute_td_pay_schedule', sanitize=False)

    @api.depends('payment_term_id.line_ids.td_milestone', 'payment_term_id.line_ids.value',
                 'payment_term_id.line_ids.value_amount', 'amount_total', 'currency_id')
    def _compute_td_pay_schedule(self):
        for order in self:
            has = bool(order.payment_term_id.line_ids.filtered('td_milestone'))
            order.td_pay_has_milestones = has
            if not has:
                order.td_pay_schedule_html = False
                continue
            rows = ''.join(
                Markup('<tr><td>%s</td><td class="text-end">%s</td><td class="text-end">%s</td></tr>') % (
                    row['milestone'], f"{row['percent']:g} %" if row['percent'] else '',
                    format_amount(order.env, row['amount'], order.currency_id or order.company_id.currency_id))
                for row in order._td_payment_schedule())
            order.td_pay_schedule_html = Markup('<table class="table table-sm mb-0 td_pay_schedule"><tbody>%s</tbody></table>') % Markup(rows)

    def _td_contract_mode(self):
        """Printed contract: «contract» (contract work, made to the measurements of the customer) or «sale» (sale
        contract) — the parameter of the company of the order (td_mebli_base, contract_mode of the questionnaire)."""
        self.ensure_one()
        mode = self.company_id.td_contract_mode
        if not mode:
            raise UserError(self.env._("Set the contract mode in the company settings (Sales → Settings)"))
        return mode

    def _td_payment_schedule(self):
        """The payment schedule of the printed contract: the lines of the standard payment terms of the order with their
        furniture milestone and the amount of the order total (percent lines) or the fixed amount."""
        self.ensure_one()
        labels = dict(self.env['account.payment.term.line']._fields['td_milestone']._description_selection(self.env))
        rows = []
        for line in self.payment_term_id.line_ids:
            amount = self.amount_total * line.value_amount / 100.0 if line.value == 'percent' else line.value_amount
            rows.append({'milestone': labels.get(line.td_milestone) or self.env._("%s days after the invoice", line.nb_days),
                         'percent': line.value_amount if line.value == 'percent' else False, 'amount': amount})
        return rows


class ReportContract(models.AbstractModel):
    """AC-034: without the contract mode of the company the PDF of the contract is not made."""
    _name = 'report.td_mebli_sale.report_contract'
    _description = 'Printed contract of the order'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].browse(docids)
        for order in docs:
            order._td_contract_mode()
        return {'doc_ids': docids, 'doc_model': 'sale.order', 'docs': docs, 'data': data}
