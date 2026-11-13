"""19.0.1.1.0: the menus move to the groups of td_mebli_base (AC-122, AC-N.07).

A `menuitem groups=` on update adds the new groups but keeps the old ones, so the dashboard menu would stay visible to
the sales and production managers of the previous version, and the shop board to every manufacturing user. The groups
of the two menus are reset to exactly the intended ones."""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    pairs = [('td_mebli_dashboard.menu_dashboard_root', 'td_mebli_dashboard.group_td_mebli_director'),
             ('td_mebli_dashboard.menu_shop_board', 'td_mebli_base.group_feature_shop_board')]
    for menu_xmlid, group_xmlid in pairs:
        menu = env.ref(menu_xmlid, raise_if_not_found=False)
        group = env.ref(group_xmlid, raise_if_not_found=False)
        if menu and group:
            menu.group_ids = [(6, 0, group.ids)]
