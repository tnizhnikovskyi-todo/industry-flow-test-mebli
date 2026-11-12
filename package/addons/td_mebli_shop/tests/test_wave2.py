from odoo.tests import tagged

from odoo.addons.td_mebli_sale.tests.common import TdMebliSaleCommon


@tagged('post_install', '-at_install')
class TestWave2Shop(TdMebliSaleCommon):
    """F-29 labels of the parts with QR, F-56 acceptance and transfer act without installation."""

    def test_labels_with_qr(self):
        order = self._make_order()
        order.action_confirm()
        order.action_td_build_kit()
        rows = order._td_label_rows()
        self.assertTrue(rows)
        self.assertTrue(all(r['code'] and r['order'] == order.name for r in rows))
        self.assertTrue(any(r['size'] for r in rows), "the size of the part is on the label")
        html, _kind = self.env['ir.actions.report']._render_qweb_html('td_mebli_shop.report_part_labels', order.ids)
        self.assertIn(b'data:image/', html, "QR from the barcode generator of the reports")
        self.assertIn(rows[0]['code'].encode(), html)
        production = order.mrp_production_ids[:1]
        self.assertEqual(len(production._td_label_rows()), len(production.bom_id.td_part_ids))
        html, _kind = self.env['ir.actions.report']._render_qweb_html('td_mebli_shop.report_mo_part_labels', production.ids)
        self.assertIn(b'td_label', html)

    def test_transfer_act_of_the_delivery(self):
        product = self.env['product.product'].create({'name': 'Dresser', 'is_storable': True, 'list_price': 5000})
        order = self.env['sale.order'].create({'partner_id': self.partner.id,
                                               'order_line': [(0, 0, {'product_id': product.id, 'product_uom_qty': 1})]})
        order.action_confirm()
        picking = order.picking_ids[:1]
        html, _kind = self.env['ir.actions.report']._render_qweb_html('td_mebli_shop.report_handover_act', picking.ids)
        self.assertIn(b'td_report_handover', html)
        self.assertIn(b'Dresser', html)
        self.assertIn(order.name.encode(), html)
