from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductCategory(models.Model):
    _inherit = 'product.category'

    td_warranty_months = fields.Integer(
        string='Warranty, Months',
        help="Warranty term of the products of this category (AC-111). Empty until the conclusion of the lawyer "
             "(No 17): the claim then shows «Warranty term is not set» and the service decides by hand.")

    @api.constrains('td_warranty_months')
    def _check_td_warranty_months(self):
        if any(category.td_warranty_months < 0 for category in self):
            raise ValidationError(self.env._("The warranty term cannot be negative."))
