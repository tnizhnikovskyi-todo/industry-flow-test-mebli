from odoo import api, fields, models
from odoo.tools import html2plaintext

ACTIVITY = 'td_mebli_notify.mail_activity_type_td_forecast_shift'


class SaleOrder(models.Model):
    """Position 1 (F-50): the salesperson gets a standard activity on the order when the forecast date (td_mebli_sale,
    read from Purchase and Manufacturing) passes the promised date; the activity is closed when the forecast comes back.
    One open activity per order: a new shift updates it, it is never duplicated. When the salesperson marks the activity
    «Done» while the forecast is still late, the cron does not open it again for the same shift: a new activity only
    when the shift grows (the handled shift is kept on the order)."""
    _inherit = 'sale.order'

    td_forecast_shift_done = fields.Integer(
        string='Handled Forecast Shift, days', copy=False, readonly=True,
        help="The shift of the forecast (days) for which the salesperson already got the activity; reset when the "
             "forecast comes back within the promised date.")

    def _td_sync_forecast_activity(self):
        if self.env.context.get('td_no_forecast_activity'):  # bulk loads (demo data, migration) run the cron after
            return
        # sudo: the activity of the salesperson is searched and created by the system (cron, writes of purchase/MO users)
        Activity = self.env['mail.activity'].sudo()
        activity_type = self.env.ref(ACTIVITY, raise_if_not_found=False)
        if not activity_type:
            return
        orders = self.filtered(lambda o: o.id and o.state == 'sale')
        # the forecast is stored (td_mebli_sale) but the purchase dates and receipts are not stored dependencies:
        # recompute it now from the documents
        self.env['purchase.order.line'].invalidate_model(['td_date_ready', 'td_supplier_delay'])
        orders._td_recompute_forecast()
        opened = Activity.search([('res_model', '=', 'sale.order'), ('res_id', 'in', orders.ids),
                                  ('activity_type_id', '=', activity_type.id)])
        by_order = {a.res_id: a for a in opened}
        for order in orders:
            current = by_order.get(order.id)
            late = order.td_delay_days > 0 and order.delivery_status != 'full'
            # D-13 (AC-N.01): the texts of the activity are in the language of the salesperson who reads it, not of
            # whoever moved the date (the cron runs as the system user, en_US)
            lang = (order.user_id or self.env.user).lang or self.env.lang
            lang_env = self.with_context(lang=lang).env
            if late:
                summary = lang_env._("Forecast later than promised by %s days", order.td_delay_days)
                note = lang_env._("Forecast date %(forecast)s, promised %(promised)s. %(reason)s",
                                  forecast=fields.Date.to_string(order.td_forecast_date),
                                  promised=fields.Date.to_string(fields.Date.context_today(order, order.commitment_date)),
                                  reason=order.td_late_item or '')
                if current:
                    # the shift or its reason (the late item) changed: the open activity says it
                    if current.summary != summary or html2plaintext(current.note or '').strip() != note.strip():
                        current.write({'summary': summary, 'note': note})
                elif order.td_delay_days > order.td_forecast_shift_done:
                    # sudo: the activity goes to the salesperson of the order also when a purchase or production user moved the date
                    order.sudo().activity_schedule(
                        ACTIVITY, date_deadline=fields.Date.context_today(order), summary=summary, note=note,
                        user_id=(order.user_id or self.env.user).id)
                else:
                    continue  # marked «Done» for this shift (or a larger one): not repeated
                if order.td_forecast_shift_done != order.td_delay_days:
                    # sudo: a technical counter of the order, written by whoever moved the date (purchase, manufacturing)
                    order.sudo().td_forecast_shift_done = order.td_delay_days
            else:
                if current:
                    # sudo: the activity of the salesperson is closed also when a purchase or production user moved the date
                    order.sudo().activity_feedback([ACTIVITY], feedback=lang_env._("The forecast date is back within "
                                                                                  "the promised date."))
                if order.td_forecast_shift_done:
                    # sudo: a technical counter of the order, written by whoever moved the date (purchase, manufacturing)
                    order.sudo().td_forecast_shift_done = 0

    @api.model
    def _cron_td_forecast_activity(self):
        self.search([('state', '=', 'sale'), ('commitment_date', '!=', False)])._td_sync_forecast_activity()

    def write(self, vals):
        result = super().write(vals)
        if 'commitment_date' in vals or 'state' in vals:
            self._td_sync_forecast_activity()
        return result

    def action_td_notify_new_date(self):
        """Position 2: the letter «new date» to the customer — the standard composer with the template; the salesperson
        decides when to tell the customer (the forecast is internal until then)."""
        self.ensure_one()
        template = self.env.ref('td_mebli_notify.mail_template_td_new_date')
        return {
            'type': 'ir.actions.act_window', 'res_model': 'mail.compose.message', 'view_mode': 'form', 'target': 'new',
            'views': [(False, 'form')],
            'name': self.env._("Letter to the Customer"),
            'context': {'default_model': 'sale.order', 'default_res_ids': self.ids, 'default_template_id': template.id,
                        'default_composition_mode': 'comment', 'default_email_layout_xmlid': 'mail.mail_notification_light',
                        'mark_so_as_sent': False},
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def write(self, vals):
        result = super().write(vals)
        if 'date_planned' in vals or 'qty_received' in vals:
            orders = self.env['sale.order']
            # sudo: read only — the sales orders of the purchase line are found also for a purchase user without sales rights
            for line in self.sudo():
                orders |= line._td_productions().reference_ids.sale_ids | line.sale_line_id.order_id
            orders._td_sync_forecast_activity()
        return result


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def write(self, vals):
        result = super().write(vals)
        if 'date_finished' in vals or 'date_start' in vals:
            # sudo: read only — the sales orders of the manufacturing order are found also for a user without sales rights
            (self.sudo().reference_ids.sale_ids | self.sudo().sale_line_id.order_id)._td_sync_forecast_activity()
        return result
