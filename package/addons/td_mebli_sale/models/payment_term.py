from odoo import fields, models

CONTRACT_PARAM = 'td_mebli_sale.contract_mode'  # «work» (contract work, default) or «sale» (sale contract)


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

    def _td_contract_mode(self):
        """Printed contract: «work» (contract work, made to the measurements of the customer) or «sale» (sale contract)."""
        return self.env['ir.config_parameter'].sudo().get_param(CONTRACT_PARAM, 'work')

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


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    td_mebli_contract_mode = fields.Selection(
        [('work', 'Contract work'), ('sale', 'Sale contract')], string='Printed Contract', default='work',
        config_parameter=CONTRACT_PARAM,
        help="Contract work: the furniture is made to the measurements of the customer (the usual case). Sale contract: "
             "ready-made furniture from the catalogue. Both texts are templates to be checked by a lawyer.")
