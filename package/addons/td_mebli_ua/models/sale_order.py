from odoo import api, fields, models
from odoo.exceptions import AccessError
from odoo.tools import float_compare, float_round, format_amount


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_order_date(self):
        """review A-14 M1: «Update Prices at the Rate» converts the currencies at today's rate without changing the date of
        the quotation — the date of the conversion comes from the context, the date of the order stays."""
        return self.env.context.get('td_rate_date') or super()._get_order_date()

    def _td_pricelist_discount(self):
        """The discount the price list gives to the line (the formula of the standard `_compute_discount`, without writing
        it): a discount that differs from it was typed by the salesperson."""
        self.ensure_one()
        if not (self.order_id.pricelist_id and self.product_uom_id and self.product_id
                and self.env['product.pricelist.item']._is_discount_feature_enabled()
                and self.pricelist_item_id._show_discount()):
            return 0.0
        line = self.with_company(self.company_id)
        base_price = line._get_pricelist_price_before_discount()
        if not base_price:
            return 0.0
        discount = (base_price - line._get_pricelist_price()) / base_price * 100
        if (discount > 0 and base_price > 0) or (discount < 0 and base_price < 0):
            return float_round(discount, precision_digits=self.env['decimal.precision'].precision_get('Discount'))
        return 0.0

    def _td_has_manual_price(self):
        """review A-14 M1: the salesperson changed the unit price (the standard mark: `technical_price_unit` differs from
        `price_unit`) or typed a discount of his own — the rate update does not touch such a line."""
        self.ensure_one()
        currency = self.currency_id or self.company_id.currency_id
        if currency.compare_amounts(self.technical_price_unit, self.price_unit):
            return True
        precision = self.env['decimal.precision'].precision_get('Discount')
        return bool(float_compare(self.discount, self._td_pricelist_discount(), precision_digits=precision))


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def td_action_update_prices_by_rate(self):
        """«Update Prices at the Rate» (AC-037): only quotations (state «Quotation» / «Quotation Sent») get the price of
        the price list at today's rate; confirmed orders are not changed. Review A-14 M1: only the lines whose price and
        discount come from the price list are recomputed — a price or a discount typed by the salesperson stays, and the
        date of the quotation is not changed. The chatter of each changed quotation gets the old and the new total and
        the number of the kept manual lines."""
        if not self.env.user.has_group('td_mebli_base.group_finance'):
            raise AccessError(self.env._("Only the finance users update the prices at the rate."))
        orders = self.search([('state', 'in', ('draft', 'sent')), ('company_id', 'in', self.env.companies.ids)])
        changed = self.browse()
        today = fields.Date.context_today(self)
        kept_total = 0
        for order in orders:
            old_total = order.amount_total
            lines = order.order_line.filtered(
                lambda ln: ln.product_id and not ln.display_type and not ln.is_downpayment and not ln.qty_invoiced
                and not ln._is_global_discount())
            manual = lines.filtered(lambda ln: ln._td_has_manual_price())
            for line in (lines - manual).with_context(td_rate_date=today):
                line.invalidate_recordset(['pricelist_item_id'])
                line.with_context(sale_write_from_compute=True)._reset_price_unit()
                line.discount = line._td_pricelist_discount()
            kept_total += len(manual)
            if float_compare(old_total, order.amount_total, precision_rounding=order.currency_id.rounding):
                body = self.env._(
                    "Prices updated at the NBU rate: total %(old)s → %(new)s.",
                    old=format_amount(self.env, old_total, order.currency_id),
                    new=format_amount(self.env, order.amount_total, order.currency_id))
                if manual:
                    body += " " + self.env._("Lines with a manual price or discount kept: %(count)s.", count=len(manual))
                order.message_post(body=body)
                changed |= order
        message = self.env._("Quotations with new prices: %(count)s of %(total)s.", count=len(changed), total=len(orders))
        if kept_total:
            message += " " + self.env._("Lines with a manual price or discount kept: %(count)s.", count=kept_total)
        return {
            'type': 'ir.actions.client', 'tag': 'display_notification',
            'params': {'type': 'success' if changed else 'info', 'sticky': False, 'message': message},
        }
