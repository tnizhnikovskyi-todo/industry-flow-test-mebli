import re

from odoo.tests import TransactionCase, tagged
from odoo.tools.misc import file_path

# D-13 (AC-N.01): the modules of the package whose texts are checked here (group T of A-11 attempt 7)
MODULES = ['td_mebli_cutting', 'td_mebli_purchase', 'td_mebli_shop', 'td_mebli_mrp', 'td_mebli_base', 'td_mebli_bas',
           'td_mebli_dashboard', 'td_mebli_notify', 'td_mebli_claim', 'td_mebli_migration', 'td_mebli_attendance',
           'td_mebli_maint', 'td_mebli_multico']


@tagged('post_install', '-at_install')
class TestUkrainianTexts(TransactionCase):
    """D-13 (AC-N.01): every text of the modules has a Ukrainian translation in i18n/uk.po (no empty msgstr), so the
    interface in uk_UA shows no English labels, titles, buttons or messages of these modules."""

    def test_d13_uk_po_has_no_empty_translation(self):
        import polib
        installed = set(self.env['ir.module.module'].search(
            [('name', 'in', MODULES), ('state', '=', 'installed')]).mapped('name'))
        for module in MODULES:
            if module not in installed:
                continue
            po = polib.pofile(file_path(f'{module}/i18n/uk.po'))
            empty = [e.msgid for e in po if not e.msgstr and re.search('[A-Za-z]{2}', e.msgid)
                     and e.msgid not in ('ID', 'PIN', 'QR', 'Odoo')]
            self.assertFalse(empty, f"{module}: texts without a Ukrainian translation: {empty[:5]}")
            # Odoo merges uk.po with the .pot of the module (odoo/tools/translate.py PoFileReader): a translation
            # whose text is not in the .pot is dropped as obsolete and the interface stays in English
            try:
                pot = polib.pofile(file_path(f'{module}/i18n/{module}.pot'))
            except FileNotFoundError:
                continue
            known = {e.msgid for e in pot}
            lost = [e.msgid for e in po if e.msgid and e.msgid not in known]
            self.assertFalse(lost, f"{module}: translations missing in {module}.pot are not loaded: {lost[:5]}")
