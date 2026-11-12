from odoo import fields, models


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    td_time_basis = fields.Selection(
        [('fixed', 'Fixed'), ('per_part', 'Per part'), ('per_edge_m', 'Per metre of edge'),
         ('per_board_m2', 'Per m2 of board')],
        string='Time Basis', default='fixed', required=True)
    td_time_rate = fields.Float(string='Minutes per Basis Unit')
    # piece rate of the operation (decision AI-08): UAH per basis unit (part, metre of edge, m2 of board) or per
    # operation when the basis is fixed; the piecework accrual multiplies it by the basis quantity of the order BoM
    td_piece_rate = fields.Float(string='Piece Rate per Basis Unit', digits=(16, 2))

    def _td_basis_quantity(self):
        """Quantity of the basis of the operation for one unit of the product of its BoM (1 for a fixed basis)."""
        self.ensure_one()
        bom = self.bom_id
        return {
            'per_part': bom.td_part_count,
            'per_edge_m': bom.td_edge_length_m,
            'per_board_m2': bom.td_board_area_m2,
        }.get(self.td_time_basis, 1.0)
