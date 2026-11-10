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
