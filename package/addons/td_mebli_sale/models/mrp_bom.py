from odoo import fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    td_sale_line_id = fields.Many2one('sale.order.line', string='Sales Order Line', readonly=True, copy=False,
                                      index=True, ondelete='set null')
    td_sale_order_id = fields.Many2one('sale.order', string='Sales Order', related='td_sale_line_id.order_id',
                                       store=True, index=True)

    def action_td_open_sale_order(self):
        self.ensure_one()
        return self.td_sale_order_id._get_records_action()
