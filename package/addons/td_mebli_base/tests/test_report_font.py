import io
import shutil
import subprocess
import tempfile

from PIL import Image

from odoo.tests import HttpCase, tagged

TEXT = 'Договір підряду: Ґанок, їжак, Єнот, щілина, ЬЮЯ'

ARCH = """<t t-name="{key}">
    <t t-foreach="docs" t-as="doc">
        <t t-call="web.basic_layout">
            <div class="page {cls}"><h2>{text}</h2><p>{text}</p><strong>{text}</strong></div>
        </t>
    </t>
</t>"""


ARCH_EXTERNAL = """<t t-name="{key}">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="doc">
            <t t-call="web.external_layout">
                <t t-set="address"><div>{text}</div></t>
                <div class="page {cls}"><h2>{text}</h2><p>{text}</p><strong>{text}</strong></div>
            </t>
        </t>
    </t>
</t>"""


@tagged('post_install', '-at_install')
class TestReportFont(HttpCase):
    """AC-N.06: a report with the class td_mebli_report is printed by wkhtmltopdf with the font of the package (Roboto
    with the full Cyrillic set): no font of the system is used as a fallback.

    wkhtmltopdf draws the glyphs of a web font as outlines, so the PDF of the package font embeds no font at all
    (pdffonts is empty) while the page has ink; the same text in the standard layout (Lato, no Cyrillic) embeds a
    font of the system — the fallback the NFR forbids."""

    def _print(self, cls, arch=ARCH, xmlid=None):
        key = 'td_mebli_base.test_font_report%s' % (cls and '_' + cls)
        if xmlid:
            key += '_' + xmlid
        self.env['ir.ui.view'].create({'name': key, 'type': 'qweb', 'key': key,
                                       'arch': arch.format(key=key, cls=cls, text=TEXT)})
        report = self.env['ir.actions.report'].create({'name': 'Font test', 'model': 'res.partner',
                                                       'report_type': 'qweb-pdf', 'report_name': key})
        if xmlid:
            # the report action of a module of the package: web.minimal_layout writes it on <body data-report-id>
            self.env['ir.model.data'].create({'module': 'td_mebli_base', 'name': xmlid, 'model': report._name,
                                              'res_id': report.id})
            report.invalidate_recordset()
            self.assertEqual(report.xml_id, 'td_mebli_base.' + xmlid)
        pdf, kind = self.env['ir.actions.report'].with_context(force_report_rendering=True)._render_qweb_pdf(
            report, self.partner.ids)
        self.assertEqual(kind, 'pdf')
        with tempfile.NamedTemporaryFile(suffix='.pdf') as file:
            file.write(pdf)
            file.flush()
            fonts = subprocess.run(['pdffonts', file.name], capture_output=True, text=True, check=True).stdout
            png = subprocess.run(['pdftoppm', '-r', '50', '-f', '1', '-l', '1', '-gray', '-png', file.name],
                                 capture_output=True, check=True).stdout
        names = [line.split()[0] for line in fonts.splitlines()[2:] if line.strip()]
        image = Image.open(io.BytesIO(png)).convert('L')
        ink = sum(1 for pixel in image.getdata() if pixel < 128)
        return names, ink

    def test_ac_n06_cyrillic_with_the_package_font(self):
        if not all(shutil.which(tool) for tool in ('pdffonts', 'pdftoppm')):
            self.skipTest("poppler-utils (pdffonts, pdftoppm) are not installed")
        if self.env['ir.actions.report'].get_wkhtmltopdf_state() != 'ok':
            self.skipTest("wkhtmltopdf is not available")
        # wkhtmltopdf loads the report assets from the server of this test
        self.env['ir.config_parameter'].sudo().set_param('report.url', self.base_url())
        self.partner = self.env['res.partner'].create({'name': 'Customer'})
        names, ink = self._print('td_mebli_report')
        self.assertEqual(names, [], "a fallback font is used in the report of the package: %s" % names)
        self.assertGreater(ink, 500, "the report of the package has no text")
        standard_names, _ink = self._print('')
        self.assertTrue(standard_names, "control: the standard layout should fall back to a font of the system")

    def test_d14_header_footer_and_address_of_a_package_report(self):
        """D-14: a report of the package on web.external_layout — the header and the footer (separate pages of
        wkhtmltopdf) with the Cyrillic name and address of the company and the address block outside the page — is
        printed without a fallback font; the same layout of a standard report keeps the company font (control)."""
        if not all(shutil.which(tool) for tool in ('pdffonts', 'pdftoppm')):
            self.skipTest("poppler-utils (pdffonts, pdftoppm) are not installed")
        if self.env['ir.actions.report'].get_wkhtmltopdf_state() != 'ok':
            self.skipTest("wkhtmltopdf is not available")
        self.env['ir.config_parameter'].sudo().set_param('report.url', self.base_url())
        self.env.company.write({'name': 'Меблева фабрика «Тест»', 'street': 'вул. Заводська, 12', 'city': 'Київ',
                                'report_footer': 'Дякуємо за замовлення: їжак, Ґанок, Єнот',
                                'external_report_layout_id': self.env.ref('web.external_layout_standard').id})
        self.partner = self.env['res.partner'].create({'name': 'Покупець Їжаченко', 'city': 'Львів'})
        names, ink = self._print('', arch=ARCH_EXTERNAL, xmlid='report_d14_layout')
        self.assertEqual(names, [], "a fallback font in the header, footer or address of a package report: %s" % names)
        self.assertGreater(ink, 500)
        standard_names, _ink = self._print('', arch=ARCH_EXTERNAL)
        self.assertTrue(standard_names, "control: the standard report keeps the layout font of the company")
