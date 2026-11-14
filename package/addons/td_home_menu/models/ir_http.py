from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        """web/models/ir_http.py session_info(): the dict becomes `session` in JS (web/static/src/session.js).
        The home screen works only on Community: with web_enterprise installed the flag is False and the JS patches
        keep the standard behaviour (README «Enterprise»)."""
        result = super().session_info()
        result['td_home_menu_active'] = self._td_home_menu_active()
        return result

    def _td_home_menu_active(self):
        return not self.env['ir.module.module'].sudo().search_count(
            [('name', '=', 'web_enterprise'), ('state', 'in', ('installed', 'to upgrade'))], limit=1)
