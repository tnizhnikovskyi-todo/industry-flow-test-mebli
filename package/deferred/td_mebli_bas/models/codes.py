from odoo import fields, models

CODE_HELP = "External code of the record in the BAS/BAF database of this company; the exchange matches by it."


class ResPartner(models.Model):
    _inherit = 'res.partner'

    td_bas_code = fields.Char(string='BAS Code', company_dependent=True, help=CODE_HELP)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    td_bas_code = fields.Char(string='BAS Code', company_dependent=True, help=CODE_HELP)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    td_bas_code = fields.Char(string='BAS Code', company_dependent=True, groups='hr.group_hr_user', help=CODE_HELP)
