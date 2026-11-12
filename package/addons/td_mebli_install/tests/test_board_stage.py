from datetime import timedelta

from odoo import fields
from odoo.tests import tagged

from odoo.addons.td_mebli_sale.tests.common import TdMebliSaleCommon

PHOTO = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='


@tagged('post_install', '-at_install')
class TestBoardStages(TdMebliSaleCommon):
    """A4 (F-07): the stages after «Made» follow the standard documents — the delivery, the act, the invoices."""

    def _made_order(self):
        env = self.env
        project = env['project.project'].create({'name': 'Installation', 'allow_billable': True})
        service = env['product.product'].create({
            'name': 'Installation', 'list_price': 0.0, 'type': 'service', 'invoice_policy': 'order',
            'service_tracking': 'task_global_project', 'project_id': project.id})
        order = self._make_order()
        order.order_line = [(0, 0, {'product_id': service.id, 'product_uom_qty': 1.0})]
        order.action_confirm()
        for production in order.mrp_production_ids:
            production.action_assign()
            production.with_context(skip_consumption=True, skip_backorder=True).button_mark_done()
        self.assertEqual(order.td_stage, 'done')
        return order

    def _deliver(self, order):
        picking = order.picking_ids.filtered(lambda p: p.picking_type_code == 'outgoing' and p.state != 'done')
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        picking.with_context(skip_backorder=True).button_validate()

    def _pay_all(self, order):
        wizard = self.env['sale.advance.payment.inv'].with_context(active_model='sale.order', active_ids=order.ids).create(
            {'advance_payment_method': 'percentage', 'amount': 100})
        wizard.create_invoices()
        invoice = order.invoice_ids.filtered(lambda m: m.state == 'draft')
        invoice.action_post()
        self.env['account.payment.register'].with_context(active_model='account.move', active_ids=invoice.ids).create(
            {'amount': invoice.amount_residual})._create_payments()

    def test_wait_shipped_install_closed(self):
        order = self._made_order()
        # the customer moves the delivery past the promised date: «Waiting for the customer»
        order.commitment_date = fields.Datetime.now()
        delivery = order.picking_ids.filtered(lambda p: p.picking_type_code == 'outgoing')
        delivery.scheduled_date = fields.Datetime.now() + timedelta(days=10)
        self.assertEqual(order.td_stage, 'wait')
        self._deliver(order)
        self.assertEqual(order.td_stage, 'shipped')
        act = self.env['td.mebli.install.act'].create({'task_id': order.tasks_ids.id, 'kind': 'final'})
        self.assertEqual(order.td_stage, 'install')
        act.write({'signature': PHOTO, 'signed_by': 'Customer'})
        act.action_sign()
        self.assertEqual(order.td_stage, 'install')  # signed, but not paid in full
        self._pay_all(order)
        order.invalidate_recordset()
        order._compute_td_stage()
        self.assertEqual(order.td_stage, 'closed')

    def test_board_shows_all_stages(self):
        stages = self.env['sale.order']._read_group_td_stage(None, [])
        self.assertEqual(stages[-5:], ['done', 'wait', 'shipped', 'install', 'closed'])
