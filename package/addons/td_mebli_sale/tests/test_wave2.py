import base64
from datetime import timedelta

from odoo import fields
from odoo.tests import tagged

from .common import TdMebliSaleCommon

PNG = base64.b64encode(bytes.fromhex(
    '89504e470d0a1a0a0000000d4948445200000001000000010806000000'
    '1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082'))


@tagged('post_install', '-at_install')
class TestWave2Sale(TdMebliSaleCommon):
    """F-63 reliability of the supplier in the forecast date, F-53 visual of the designer in the quotation PDF."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.supplier = env['res.partner'].create({'name': 'Late stone shop'})
        cls.worktop = env['product.product'].create({
            'name': 'Worktop', 'type': 'consu', 'is_storable': True, 'standard_price': 900.0,
            'route_ids': [(6, 0, [env.ref('stock.route_warehouse0_mto').id, env.ref('purchase_stock.route_warehouse0_buy').id])],
            'seller_ids': [(0, 0, {'partner_id': cls.supplier.id, 'price': 900.0, 'delay': 10})],
        })
        cls.template_bom.write({'produce_delay': 5, 'bom_line_ids': [(0, 0, {'product_id': cls.worktop.id, 'product_qty': 1.0})]})

    def _history(self, days_late):
        """A received purchase of the supplier: the receipt is late by days_late against the expected arrival."""
        planned = fields.Datetime.now() - timedelta(days=40)
        purchase = self.env['purchase.order'].create({'partner_id': self.supplier.id, 'order_line': [(0, 0, {
            'product_id': self.worktop.id, 'product_qty': 1.0, 'price_unit': 900.0, 'date_planned': planned})]})
        purchase.button_confirm()
        picking = purchase.picking_ids
        picking.move_ids.quantity = 1.0
        picking.move_ids.picked = True
        picking.button_validate()
        picking.move_ids.write({'date': planned + timedelta(days=days_late)})

    def test_supplier_delay_moves_the_forecast(self):
        self._history(6)
        self._history(4)
        self.assertAlmostEqual(self.supplier.td_supplier_delay_avg, 5.0)
        self.assertEqual(self.supplier.td_supplier_delay_lines, 2)
        order = self._make_order()
        start = fields.Date.context_today(order, order.date_order)
        order.commitment_date = fields.Datetime.to_datetime(start + timedelta(days=60))
        order.action_confirm()
        line = order._get_purchase_orders().order_line.filtered(lambda l: l.product_id == self.worktop)
        line.date_planned = fields.Datetime.to_datetime(start + timedelta(days=20))
        line.invalidate_recordset()
        self.assertEqual(line.td_supplier_delay, 5)
        self.assertEqual(line.td_date_ready, start + timedelta(days=20 + 5 + 5),
                         "supplier date + average delay of the supplier + manufacturing lead time")

    def test_early_deliveries_count_as_on_time(self):
        self._history(-3)
        self.assertEqual(self.supplier.td_supplier_delay_avg, 0.0)

    def test_design_visual_in_the_quotation(self):
        order = self._make_order()
        html, _kind = self.env['ir.actions.report']._render_qweb_html('sale.report_saleorder', order.ids)
        self.assertNotIn(b'td_design_visual', html)
        order.td_design_image = PNG
        html, _kind = self.env['ir.actions.report']._render_qweb_html('sale.report_saleorder', order.ids)
        self.assertIn(b'td_design_visual', html)
