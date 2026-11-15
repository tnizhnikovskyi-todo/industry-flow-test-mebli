import re

from odoo.tests import TransactionCase, tagged
from odoo.tools.misc import file_path

PALETTE = {'#985184', '#005E7A', '#1AD3BB', '#FBB945', '#F86126', '#FC868B', '#FFFFFF'}


@tagged('post_install', '-at_install')
class TestAppIcon(TransactionCase):

    def test_root_menu_icon(self):
        """A-11-fix4: own icon in the style of the standard Odoo 19 icons (no plate, palette), png + svg."""
        menu = self.env.ref('td_mebli_measure.td_mebli_measure_root_menu')
        self.assertEqual(menu.web_icon, 'td_mebli_measure,static/description/icon.png')
        self.assertTrue(menu.web_icon_data)
        self.assertTrue(file_path('td_mebli_measure/static/description/icon.png'))
        with open(file_path('td_mebli_measure/static/description/icon.svg'), encoding='utf-8') as svg_file:
            svg = svg_file.read()
        self.assertIn('viewBox="0 0 50 50"', svg)
        colors = {c.upper() for c in re.findall(r'#[0-9A-Fa-f]{6}', svg)}
        self.assertLessEqual(colors, PALETTE)
