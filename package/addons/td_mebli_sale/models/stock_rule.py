from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_matching_bom(self, product_id, company_id, values):
        """Use the order BoM of the sales order line that triggered the procurement chain."""
        sale_line_id = values.get('sale_line_id')
        if not sale_line_id and values.get('move_dest_ids'):
            sale_line_id = values['move_dest_ids'][:1].sale_line_id.id
        if sale_line_id:
            line = self.env['sale.order.line'].browse(sale_line_id)
            if line.td_bom_id and line.product_id == product_id:
                return line.td_bom_id
        return super()._get_matching_bom(product_id, company_id, values)
