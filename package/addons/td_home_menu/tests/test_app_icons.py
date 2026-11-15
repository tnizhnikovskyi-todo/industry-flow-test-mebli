import re

from odoo.tests import TransactionCase, tagged
from odoo.tools.misc import file_path

# the style of the standard icons of Odoo 19 (A-11-fix4): no background plate, flat shapes of this palette
PALETTE = {'#985184', '#005E7A', '#1AD3BB', '#FBB945', '#F86126', '#FC868B', '#FFFFFF'}


def td_root_menus(env):
    """Root menus (no parent) created by ToDo modules td_*."""
    data = env['ir.model.data'].search([('model', '=', 'ir.ui.menu'), ('module', '=like', 'td\\_%')])
    menus = env['ir.ui.menu'].browse(data.mapped('res_id')).exists().filtered(lambda m: not m.parent_id)
    xmlids = {d.res_id: f'{d.module}.{d.name}' for d in data}
    return menus, xmlids


def check_app_icon(case, menu, xmlid):
    """web_icon «<module>,static/description/icon.png» of the own module; icon.png and icon.svg exist;
    the svg is 50×50, without a plate and in the palette; the menu has the image loaded."""
    module = xmlid.split('.')[0]
    case.assertTrue(menu.web_icon, f'{xmlid}: a root menu without web_icon')
    icon_module, icon_path = menu.web_icon.split(',')
    case.assertEqual(icon_module, module, f'{xmlid}: the icon is borrowed from {icon_module}')
    case.assertEqual(icon_path, 'static/description/icon.png', xmlid)
    case.assertTrue(file_path(f'{module}/static/description/icon.png'))
    with open(file_path(f'{module}/static/description/icon.svg'), encoding='utf-8') as svg_file:
        svg = svg_file.read()
    case.assertIn('viewBox="0 0 50 50"', svg, xmlid)
    case.assertNotIn('<rect width="50" height="50"', svg, f'{xmlid}: a background plate')
    colors = {c.upper() for c in re.findall(r'#[0-9A-Fa-f]{6}', svg)}
    case.assertLessEqual(colors, PALETTE, f'{xmlid}: colours outside the palette {colors - PALETTE}')
    case.assertTrue(menu.web_icon_data, f'{xmlid}: the image of the icon is not loaded')


@tagged('post_install', '-at_install')
class TestAppIcons(TransactionCase):

    def test_td_root_menus_have_own_icons(self):
        menus, xmlids = td_root_menus(self.env)
        for menu in menus:
            with self.subTest(menu=xmlids[menu.id]):
                check_app_icon(self, menu, xmlids[menu.id])

    def test_caption_breaks_between_words(self):
        """A-11-fix4: «Обслуговувань / я» — no break inside a word."""
        with open(file_path('td_home_menu/static/src/home_menu/home_menu.scss'), encoding='utf-8') as scss_file:
            scss = scss_file.read()
        self.assertNotIn('anywhere', scss)
        self.assertIn('overflow-wrap: normal', scss)
        self.assertIn('word-break: normal', scss)
        self.assertIn('hyphens: auto', scss)
