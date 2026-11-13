from odoo.tests import tagged

from odoo.addons.td_mebli_sale.tests.common import TdMebliSaleCommon


@tagged('post_install', '-at_install')
class TestKitReport(TdMebliSaleCommon):
    """A2: the printed packing list — places, items, labels, packed or not."""

    def test_packing_list_prints_places(self):
        order = self._make_order()
        order.action_confirm()
        order.action_td_build_kit()
        lines = order.td_kit_line_ids
        self.assertTrue(lines)
        lines[:1].packed = True
        groups = order._td_kit_by_place()
        self.assertEqual([place for place, _lines in groups], sorted(set(lines.mapped('place'))))
        html, _kind = self.env['ir.actions.report']._render_qweb_html('td_mebli_shop.report_kit', order.ids)
        self.assertIn(lines[:1].label.encode(), html)
        self.assertIn('✓'.encode(), html)
