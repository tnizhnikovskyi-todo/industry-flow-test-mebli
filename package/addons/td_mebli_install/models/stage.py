from odoo import api, fields, models

from .payment import ROUNDING


class SaleOrder(models.Model):
    """F-07: the stages of the order board after «Made» are read from the standard documents, not set by hand.

    Waiting for the customer: made, the delivery (stock.picking) is moved by the customer past the promised date.
    Shipped / on delivery: the delivery is done, the crew has not started. Installation: an act of the visit is open or
    signed while the order is not paid in full. Closed: the order is paid in full and its final act is signed (or it is
    delivered and has no open visit)."""
    _inherit = 'sale.order'

    # reverse of the stored project.task.sale_order_id (sale_project): the visits of the order, a dependency of the stage
    td_task_ids = fields.One2many('project.task', 'sale_order_id', string='Visits')
    td_stage = fields.Selection(
        selection_add=[('done',), ('wait', 'Waiting for the customer'), ('shipped', 'Shipped / on delivery'),
                       ('install', 'Installation'), ('closed', 'Closed')],
        ondelete={'wait': lambda orders: orders.write({'td_stage': 'done'}),
                  'shipped': lambda orders: orders.write({'td_stage': 'done'}),
                  'install': lambda orders: orders.write({'td_stage': 'done'}),
                  'closed': lambda orders: orders.write({'td_stage': 'done'})})

    @api.depends('picking_ids.state', 'picking_ids.scheduled_date', 'commitment_date', 'amount_total',
                 'td_act_ids.state', 'td_act_ids.kind', 'td_task_ids.state', 'order_line.invoice_lines.move_id.payment_state',
                 'order_line.invoice_lines.move_id.amount_residual')
    def _compute_td_stage(self):
        super()._compute_td_stage()
        for order in self.filtered(lambda o: o.td_stage == 'done'):
            order.td_stage = order._td_stage_after_made()

    def _td_stage_after_made(self):
        self.ensure_one()
        order = self.sudo()  # read only: the stage is shown to the salesperson, the documents stay with their modules
        deliveries = order.picking_ids.filtered(lambda p: p.picking_type_code == 'outgoing' and p.state != 'cancel')
        delivered = bool(deliveries) and all(p.state == 'done' for p in deliveries)
        paid_full = order._td_paid_amount() >= order.amount_total - ROUNDING
        final_signed = order.td_act_ids.filtered(lambda a: a.kind == 'final' and a.state == 'signed')
        visits_open = order.td_task_ids.filtered(lambda t: t.state not in ('1_done', '1_canceled'))
        if paid_full and (final_signed or (delivered and not order.td_act_ids and not visits_open)):
            return 'closed'
        if order.td_act_ids:
            return 'install'
        if delivered:
            return 'shipped'
        pending = deliveries.filtered(lambda p: p.state != 'done' and p.scheduled_date)
        if order.commitment_date and pending and min(pending.mapped('scheduled_date')).date() > order.commitment_date.date():
            return 'wait'
        return 'done'
