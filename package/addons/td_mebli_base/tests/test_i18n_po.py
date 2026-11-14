import os
import re

from odoo.tests import TransactionCase, tagged
from odoo.tools.misc import file_path
from odoo.tools.translate import TranslationModuleReader

IGNORED = ('ID', 'PIN', 'QR', 'Odoo')


def _latin(text):
    return bool(re.search('[A-Za-z]{2}', text)) and text not in IGNORED


@tagged('post_install', '-at_install')
class TestUkrainianTexts(TransactionCase):
    """D-13, D-16 (AC-N.01): every installed module of the package (td_mebli_*) has an i18n/<module>.pot with every text
    Odoo exports for the module now (fields, views, menus, actions, data, code) and a Ukrainian translation of each of them
    in i18n/uk.po (no empty msgstr), so the interface in uk_UA shows no English labels, tabs, titles, buttons or messages."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.modules = cls.env['ir.module.module'].search(
            [('name', '=like', 'td_mebli_%'), ('state', '=', 'installed')]).mapped('name')

    def _po(self, path):
        import polib
        return polib.pofile(path)

    def test_d13_uk_po_has_no_empty_translation(self):
        for module in self.modules:
            if not os.path.exists(os.path.join(os.path.dirname(file_path(f'{module}/__manifest__.py')), 'i18n', 'uk.po')):
                continue
            po = self._po(file_path(f'{module}/i18n/uk.po'))
            empty = [e.msgid for e in po if not e.msgstr and _latin(e.msgid)]
            self.assertFalse(empty, f"{module}: texts without a Ukrainian translation: {empty[:5]}")

    def test_d16_pot_and_uk_po_cover_every_exported_text(self):
        """Odoo merges uk.po with the .pot of the module (odoo/tools/translate.py PoFileReader): a translation whose
        text is not in the .pot is dropped as obsolete (D-16: «Cost of the Order», «Payment Schedule» of td_mebli_sale)."""
        for module in self.modules:
            exported = {row[4] for row in TranslationModuleReader(self.env.cr, modules=[module])
                        if row[0] == module and _latin(row[4])}
            if not exported:  # e.g. td_mebli_demo: Ukrainian demo data only, nothing to translate
                continue
            pot_path = os.path.join(os.path.dirname(file_path(f'{module}/i18n/uk.po')), f'{module}.pot')
            self.assertTrue(os.path.exists(pot_path), f"{module}: no i18n/{module}.pot")
            pot = {e.msgid for e in self._po(pot_path)}
            missing_pot = sorted(exported - pot)
            self.assertFalse(missing_pot, f"{module}: texts missing in {module}.pot: {missing_pot[:5]}")
            uk = {e.msgid for e in self._po(file_path(f'{module}/i18n/uk.po')) if e.msgstr}
            missing_uk = sorted(exported - uk)
            self.assertFalse(missing_uk, f"{module}: texts without a translation in uk.po: {missing_uk[:5]}")
            lost = sorted(uk - pot)
            self.assertFalse(lost, f"{module}: translations missing in {module}.pot are not loaded: {lost[:5]}")

    def test_d16_labels_in_ukrainian_in_the_database(self):
        """The labels of D-16 reach the database in uk_UA when the translations of td_mebli_sale are loaded."""
        if 'td_mebli_sale' not in self.modules:
            self.skipTest("td_mebli_sale is not installed")
        self.env['res.lang']._activate_lang('uk_UA')
        self.env['ir.module.module'].search([('name', '=', 'td_mebli_sale')])._update_translations(['uk_UA'], True)
        field = self.env['ir.model.fields']._get('sale.order', 'td_pay_schedule_html').with_context(lang='uk_UA')
        self.assertEqual(field.field_description, 'Графік оплат')
        arch = self.env.ref('td_mebli_sale.view_order_form_td_mebli').with_context(lang='uk_UA').arch_db
        self.assertNotIn('Cost of the Order', arch)
        self.assertIn('Собівартість', arch)
