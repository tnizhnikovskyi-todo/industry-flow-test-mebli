from odoo import api, fields, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    td_cutting_job_ids = fields.Many2many('td.mebli.cutting.job', string='Cutting Jobs', copy=False,
                                          relation='td_mebli_cutting_job_production_rel',
                                          column1='production_id', column2='job_id')
    td_cutting_job_count = fields.Integer(compute='_compute_td_cutting_job_count')

    @api.depends('td_cutting_job_ids')
    def _compute_td_cutting_job_count(self):
        for production in self:
            production.td_cutting_job_count = len(production.td_cutting_job_ids)

    def action_td_create_cutting_job(self):
        # AC-054: a manufacturing order without parts is named, nothing is created
        for production in self:
            if not production.bom_id.td_part_ids:
                raise UserError(self.env._("There are no cutting parts in manufacturing order %s", production.name))
        productions = self.filtered(lambda mo: mo.state in ('confirmed', 'progress', 'to_close'))
        if not productions:
            raise UserError(self.env._("Select confirmed manufacturing orders that have an order BoM with parts."))
        job = self.env['td.mebli.cutting.job'].create({'production_ids': [(6, 0, productions.ids)]})
        return job._get_records_action(name=self.env._("Cutting Job"))

    def action_td_view_cutting_jobs(self):
        self.ensure_one()
        return self.td_cutting_job_ids._get_records_action(name=self.env._("Cutting Jobs"))

    def _td_material_cost(self):
        """Standard cost of the components reserved (or planned) for the order."""
        self.ensure_one()
        total = 0.0
        for move in self.move_raw_ids.filtered(lambda m: m.state != 'cancel'):
            quantity = sum(move.move_line_ids.mapped('quantity')) or move.product_uom_qty
            total += quantity * move.product_id.uom_id._compute_price(move.product_id.standard_price, move.product_uom)
        return total
