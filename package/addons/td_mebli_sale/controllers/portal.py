import binascii

from odoo import http
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class TdMebliChangePortal(CustomerPortal):
    """AC-120: the customer signs a fixed change of his order in the standard portal of the order (the access token of
    the order, as the standard signature of a quotation: sale/controllers/portal.py portal_quote_accept)."""

    @http.route(['/my/orders/<int:order_id>/change/<int:change_id>/sign'], type='jsonrpc', auth='public', website=True)
    def td_portal_change_sign(self, order_id, change_id, access_token=None, name=None, signature=None):
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': request.env._('Invalid order.')}
        change = order_sudo.td_change_ids.filtered(lambda c: c.id == change_id)
        if not change:
            return {'error': request.env._('Invalid order.')}
        try:
            change._td_sign(name, signature)
            request.env.cr.flush()
        except UserError as error:
            return {'error': str(error)}
        except (TypeError, binascii.Error):
            return {'error': request.env._('Invalid signature data.')}
        return {'force_refresh': True, 'redirect_url': order_sudo.get_portal_url(query_string='&message=sign_ok')}
