from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    td_length_mm = fields.Integer(string='Length, mm', aggregator=None)
    td_width_mm = fields.Integer(string='Width, mm', aggregator=None)
    td_is_offcut = fields.Boolean(string='Business Offcut', index=True)
    td_cutting_job_id = fields.Many2one('td.mebli.cutting.job', string='Cutting Job', readonly=True,
                                        copy=False, ondelete='set null')
    td_area_m2 = fields.Float(string='Area, m2', compute='_compute_td_area_m2', digits=(16, 3))

    @api.depends('td_length_mm', 'td_width_mm')
    def _compute_td_area_m2(self):
        for lot in self:
            lot.td_area_m2 = lot.td_length_mm * lot.td_width_mm / 1_000_000.0

    td_reserved_m2 = fields.Float(string='Reserved, m2', compute='_compute_td_reserved', digits=(16, 2))
    td_reserved_for = fields.Char(string='Reserved For', compute='_compute_td_reserved')

    def _compute_td_reserved(self):
        """What of the lot is already reserved by manufacturing orders (a business offcut promised to a cutting job)."""
        lines = self.env['stock.move.line'].sudo().search([
            ('lot_id', 'in', self.ids), ('state', 'not in', ('draft', 'done', 'cancel')), ('quantity', '>', 0)])
        for lot in self:
            mine = lines.filtered(lambda line: line.lot_id == lot)
            lot.td_reserved_m2 = sum(mine.mapped('quantity'))
            lot.td_reserved_for = ', '.join(sorted(set(mine.move_id.raw_material_production_id.mapped('name'))))
