from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # the parts of the bill of materials of the order, shown where the shop works (read only, nothing is stored or entered);
    # the parts are per piece of the bill of materials, the totals are for the whole manufacturing order
    td_part_ids = fields.One2many(related='bom_id.td_part_ids', string='Parts', readonly=True)
    td_part_count = fields.Integer(string='Part Count', compute='_compute_td_part_totals',
                                   help="Parts of the whole manufacturing order: parts of one piece times the quantity.")
    td_board_area_m2 = fields.Float(string='Board Area, m2', compute='_compute_td_part_totals', digits=(16, 3))
    td_edge_length_m = fields.Float(string='Edge, m', compute='_compute_td_part_totals', digits=(16, 3))

    @api.depends('product_qty', 'product_uom_id', 'bom_id.product_qty', 'bom_id.product_uom_id',
                 'bom_id.td_part_count', 'bom_id.td_board_area_m2', 'bom_id.td_edge_length_m')
    def _compute_td_part_totals(self):
        for production in self:
            bom = production.bom_id
            factor = 0.0
            if bom.td_part_ids and bom.product_qty:
                qty = production.product_uom_id._compute_quantity(production.product_qty, bom.product_uom_id) \
                    if production.product_uom_id and bom.product_uom_id else production.product_qty
                factor = qty / bom.product_qty
            production.td_part_count = round(bom.td_part_count * factor)
            production.td_board_area_m2 = bom.td_board_area_m2 * factor
            production.td_edge_length_m = bom.td_edge_length_m * factor


class StockMove(models.Model):
    _inherit = 'stock.move'

    td_from_parts = fields.Boolean(
        string='From Parts', compute='_compute_td_from_parts',
        help="Read only: the quantity of this board or edge banding comes from the parts of the bill of materials "
             "(tab Parts of the manufacturing order).")

    @api.depends('bom_line_id.td_from_parts')
    def _compute_td_from_parts(self):
        for move in self:
            move.td_from_parts = move.bom_line_id.td_from_parts
