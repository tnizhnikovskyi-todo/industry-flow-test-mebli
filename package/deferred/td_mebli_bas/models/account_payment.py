from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    td_bas_ref = fields.Char(string='BAS Reference', readonly=True, copy=False, index='btree_not_null',
                             help="Reference of the payment in BAS: a repeated import does not double the payment.")
