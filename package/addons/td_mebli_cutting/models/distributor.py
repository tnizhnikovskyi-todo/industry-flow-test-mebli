import math
from datetime import timedelta

from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError

WORKDAY_MINUTES = 8 * 60  # one shift: the expected work of the order after the cutting, in working days


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    td_material_kind = fields.Selection(selection_add=[('cutting', 'Cutting service')],
                                        ondelete={'cutting': 'set null'})


class TdMebliCuttingJob(models.Model):
    """F-28: the cutting at the distributor is a standard purchase of a service.

    The service product «cutting» has the distributor as its vendor (product.supplierinfo with the lead time); «Send to the
    distributor» makes a standard purchase order, and the expected return of the parts is the date of its line
    (purchase.order.line.date_planned: from the vendor lead time, changed by the buyer in Purchase). The job only links
    the purchase and reads the date — nothing is entered twice."""
    _inherit = 'td.mebli.cutting.job'

    purchase_id = fields.Many2one('purchase.order', string='Distributor Order', readonly=True, copy=False,
                                  index='btree_not_null',
                                  help='The purchase of the cutting service from the distributor (Purchase).')
    distributor_id = fields.Many2one(related='purchase_id.partner_id', string='Distributor')
    return_date = fields.Date(
        string='Parts Expected Back', compute='_compute_return_date',
        help="Read only: the expected date of the cutting service line in the distributor purchase order. Empty once the "
             "parts are back (result received).")

    @api.depends('purchase_id.order_line.date_planned', 'state')
    def _compute_return_date(self):
        for job in self:
            lines = job.purchase_id.order_line.filtered(lambda line: line.date_planned and line.state != 'cancel')
            job.return_date = fields.Date.context_today(job, max(lines.mapped('date_planned'))) \
                if lines and job.state == 'sent' else False

    @api.model
    def _td_cutting_service(self):
        product = self.env['product.product'].search(
            [('td_material_kind', '=', 'cutting'), ('seller_ids', '!=', False),
             ('company_id', 'in', (False, self.env.company.id))], limit=1)
        if not product:
            raise UserError(self.env._(
                "No cutting service with a distributor: create a service product of the kind «Cutting service» "
                "with the distributor as its vendor (Purchase tab, with the lead time)."))
        return product

    def action_send_distributor(self):
        """Order the cutting from the distributor: a standard purchase order of the cutting service, then the file."""
        self._check_state('draft')
        product = self._td_cutting_service()
        seller = product.seller_ids[:1]
        for job in self:
            if not job.part_count:
                raise UserError(self.env._("%s has no parts to cut.", job.name))
            purchase = self.env['purchase.order'].create({
                'partner_id': seller.partner_id.id,
                'origin': job.name,
                'order_line': [(0, 0, {
                    'product_id': product.id, 'product_qty': 1.0,
                    'name': self.env._("%(service)s: %(job)s, %(parts)s parts",
                                       service=product.name, job=job.name, parts=job.part_count)})],
            })
            purchase.button_confirm()
            job.purchase_id = purchase
            job.action_send()
            purchase.message_post(body=Markup('%s') % self.env._("The cutting file of %s is attached.", job.name),
                                  attachment_ids=job.export_attachment_id.copy({'res_model': 'purchase.order',
                                                                                'res_id': purchase.id}).ids)
        return True

    def action_view_purchase(self):
        self.ensure_one()
        return self.purchase_id._get_records_action(name=self.env._("Distributor Order"))


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _td_days_after_cutting(self):
        """Days the workshop needs once the parts are cut: the BoM lead time, else the expected time of the open work
        orders (standard duration_expected) in working days of WORKDAY_MINUTES, at least one day."""
        self.ensure_one()
        if self.bom_id.produce_delay:
            return math.ceil(self.bom_id.produce_delay)
        minutes = sum(self.workorder_ids.filtered(lambda w: w.state not in ('done', 'cancel')).mapped('duration_expected'))
        return max(1, math.ceil(minutes / WORKDAY_MINUTES))


class SaleOrder(models.Model):
    """S-02: the cutting at the distributor moves the workshop date of the order (F-28).

    The parts are back on the expected date of the distributor purchase; the workshop needs the manufacturing lead time
    of the bill of materials after that (standard produce_delay, the same assumption as for a purchased item), or, when
    the BoM has none, the expected time of its open work orders (standard duration_expected) in shifts."""
    _inherit = 'sale.order'

    td_delay_reason = fields.Selection(selection_add=[('cutting', 'Cutting at the distributor')])

    def _td_cutting_ready(self):
        """(date, job): the latest date the workshop is ready after the parts come back from the distributor."""
        self.ensure_one()
        best, best_job = False, self.env['td.mebli.cutting.job']
        # sudo: read only — the salesperson sees the date, the cutting jobs and the purchase stay with their users
        for production in self.sudo().mrp_production_ids.filtered(lambda p: p.state not in ('done', 'cancel')):
            for job in production.td_cutting_job_ids.filtered(lambda j: j.state == 'sent' and j.return_date):
                ready = job.return_date + timedelta(days=production._td_days_after_cutting())
                if not best or ready > best:
                    best, best_job = ready, job
        return best, best_job

    def _td_shop_date(self):
        shop = super()._td_shop_date()
        cutting, _job = self._td_cutting_ready()
        return max(shop, cutting) if cutting else shop

    def _compute_td_forecast(self):
        super()._compute_td_forecast()
        for order in self.filtered(lambda o: o.td_delay_reason == 'company'):
            cutting, job = order._td_cutting_ready()
            if cutting and cutting >= order.td_forecast_date:
                order.td_delay_reason = 'cutting'
                order.td_late_item = f"{job.name} — {job.distributor_id.name}"
