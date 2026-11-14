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

    def test_d14_packing_list_and_labels_use_the_package_font(self):
        """D-14 (AC-N.06): the packing list and the part labels carry the class of the package font on the page and
        are actions of a td_mebli_* module (web.minimal_layout: <body data-report-id> — the font of the whole sheet,
        td_mebli_base/static/src/scss/td_mebli_report.scss; printing with wkhtmltopdf — td_mebli_base TestReportFont)."""
        order = self._make_order()
        order.action_confirm()
        order.action_td_build_kit()
        for xmlid, report_name in (('td_mebli_shop.action_report_kit', 'td_mebli_shop.report_kit'),
                                   ('td_mebli_shop.action_report_part_labels', 'td_mebli_shop.report_part_labels')):
            report = self.env.ref(xmlid)
            self.assertTrue(report.xml_id.startswith('td_mebli_'))
            html, _kind = self.env['ir.actions.report']._render_qweb_html(report_name, order.ids)
            self.assertIn(b'td_mebli_report', html, report_name)
