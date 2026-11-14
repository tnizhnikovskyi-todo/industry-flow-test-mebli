from odoo import api, models


class IrUiMenu(models.Model):
    """D-07 (A-11-7): «Update Prices at the Rate» is seen by the finance (the group of the menu) and only while the box
    function «NBU rates» (VP-02, td_mebli_base.group_feature_nbu) is on: the groups of a menu are OR, the function is AND."""
    _inherit = 'ir.ui.menu'

    @api.model
    def _visible_menu_ids(self, debug=False):
        visible = super()._visible_menu_ids(debug)
        menu = self.env.ref('td_mebli_ua.menu_td_update_prices_by_rate', raise_if_not_found=False)
        if menu and menu.id in visible and not self.env.user.has_group('td_mebli_base.group_feature_nbu'):
            visible = type(visible)(set(visible) - {menu.id})
        return visible
