from unittest.mock import patch

from reportlab.graphics.renderPM import RenderPMError

from odoo.tests import tagged

from odoo.addons.td_mebli_shop.models.labels import one_per_piece

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
        parts = production.bom_id.td_part_ids
        pieces = sum(int(p.qty * production.product_qty) if float(p.qty * production.product_qty).is_integer() else 1
                     for p in parts)
        self.assertEqual(len(production._td_label_rows()), pieces, "one label per piece of every part")
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

    def test_one_label_per_piece_and_qr_without_png_backend(self):
        rows = one_per_piece([{'code': 'K-1', 'qty': 2}, {'code': 'K-2', 'qty': 1}, {'code': 'K-3', 'qty': 1.5}])
        self.assertEqual([(r['code'], r['piece']) for r in rows], [('K-1', '1/2'), ('K-1', '2/2'), ('K-2', ''), ('K-3', '')])
        self.assertEqual(rows[-1]['qty'], 1.5, "a fractional quantity stays one label")
        Report = self.env['ir.actions.report']
        with patch.object(type(Report), 'barcode', side_effect=RenderPMError('no backend')):
            self.assertTrue(Report._td_qr_data_uri('K-1').startswith('data:image/svg+xml'))
        with patch.object(type(Report), 'barcode', side_effect=KeyError('a real bug')):
            with self.assertRaises(KeyError, msg="only the missing PNG backend falls back to SVG"):
                Report._td_qr_data_uri('K-1')
