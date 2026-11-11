from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    td_partner_id = fields.Many2one('res.partner', string='Customer', compute='_compute_td_partner')

    def _compute_td_partner(self):
        for production in self:
            production.td_partner_id = (production.sudo().reference_ids.sale_ids | production.sudo().sale_line_id.order_id)[:1].partner_id
