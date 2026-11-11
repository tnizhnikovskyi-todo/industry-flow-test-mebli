from odoo import fields, models


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    td_time_basis = fields.Selection(
        [('fixed', 'Fixed'), ('per_part', 'Per part'), ('per_edge_m', 'Per metre of edge'),
         ('per_board_m2', 'Per m2 of board')],
        string='Time Basis', default='fixed', required=True)
    td_time_rate = fields.Float(string='Minutes per Basis Unit')
