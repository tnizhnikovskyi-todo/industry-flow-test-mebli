from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        """web/models/ir_http.py session_info(): the dict becomes `session` in JS (web/static/src/session.js).
        The home screen works only on Community: with web_enterprise installed the flag is False and the JS patches
        keep the standard behaviour (README «Enterprise»)."""
        result = super().session_info()
        result['td_home_menu_active'] = self._td_home_menu_active()
        # owner remark 2026-11-16 (A-17 №17): the Enterprise-like look of forms and lists and the resizable chatter;
        # one switch — system parameter td_home_menu.ee_look (on by default; «False» turns it off)
        result['td_ee_look'] = result['td_home_menu_active'] and self._td_ee_look()
        return result

    def _td_ee_look(self):
        value = self.env['ir.config_parameter'].sudo().get_param('td_home_menu.ee_look', 'True')
        return str(value).strip().lower() not in ('false', '0', 'no', '')

    def _td_home_menu_active(self):
        return not self.env['ir.module.module'].sudo().search_count(
            [('name', '=', 'web_enterprise'), ('state', 'in', ('installed', 'to upgrade'))], limit=1)
