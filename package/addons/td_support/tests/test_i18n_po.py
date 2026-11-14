import os
import re

from odoo.tests import TransactionCase, tagged
from odoo.tools.misc import file_path
from odoo.tools.translate import TranslationModuleReader

MODULE = 'td_support'
IGNORED = ('ID', 'https://...', 'support@example.com')


def _latin(text):
    return bool(re.search('[A-Za-z]{2}', text)) and text not in IGNORED


@tagged('post_install', '-at_install')
class TestUkrainianTexts(TransactionCase):
    """Every text Odoo exports for the module (fields, views, menus, JS, templates) is in i18n/<module>.pot and has a
    Ukrainian translation in i18n/uk.po: the interface in uk_UA has no English labels."""

    def test_uk_po_complete(self):
        import polib
        folder = os.path.dirname(file_path(f'{MODULE}/__manifest__.py'))
        pot = {e.msgid for e in polib.pofile(os.path.join(folder, 'i18n', f'{MODULE}.pot'))}
        po = polib.pofile(os.path.join(folder, 'i18n', 'uk.po'))
        empty = [e.msgid for e in po if not e.msgstr and _latin(e.msgid)]
        self.assertFalse(empty, f'texts without a Ukrainian translation: {empty[:5]}')
        exported = {row[4] for row in TranslationModuleReader(self.env.cr, modules=[MODULE])
                    if row[0] == MODULE and _latin(row[4])}
        self.assertFalse(sorted(exported - pot), 'texts missing in the .pot: export the .pot again')
        self.assertFalse(sorted(exported - {e.msgid for e in po if e.msgstr}), 'texts missing in uk.po')
