from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class TdMebliPart(models.Model):
    _inherit = 'td.mebli.part'

    # AC-057: in a cutting job of several orders every part keeps its manufacturing order and its sales order
    td_production_id = fields.Many2one('mrp.production', string='Manufacturing Order', compute='_compute_td_production')
    td_order_name = fields.Char(string='Order', compute='_compute_td_production')

    @api.depends('bom_id')
    def _compute_td_production(self):
        productions = self.env['mrp.production'].sudo().search(
            [('bom_id', 'in', self.bom_id.ids), ('state', '!=', 'cancel')], order='id')
        by_bom = {}
        for production in productions:
            by_bom.setdefault(production.bom_id.id, production)
        for part in self:
            production = by_bom.get(part.bom_id.id, self.env['mrp.production'])
            part.td_production_id = production
            orders = production._td_sale_orders() if production else self.env['sale.order']
            part.td_order_name = ', '.join(orders.mapped('name')) or production.origin or False

    def action_td_pick_offcut(self):
        """AC-060: «Pick an offcut» on a part of a cutting job (box B, business offcuts)."""
        self.ensure_one()
        job = self.env['td.mebli.cutting.job'].browse(self.env.context.get('td_job_id'))
        if not job:
            raise UserError(self.env._("Open the part from its cutting job."))
        wizard = self.env['td.mebli.offcut.pick'].create({'job_id': job.id, 'part_id': self.id})
        return {'type': 'ir.actions.act_window', 'res_model': wizard._name, 'res_id': wizard.id, 'view_mode': 'form',
                'target': 'new', 'name': self.env._("Pick an Offcut")}


class TdMebliOffcutPick(models.TransientModel):
    _name = 'td.mebli.offcut.pick'
    _description = 'Pick a Business Offcut for a Part'

    job_id = fields.Many2one('td.mebli.cutting.job', string='Cutting Job', required=True)
    part_id = fields.Many2one('td.mebli.part', string='Part', required=True)
    candidate_ids = fields.Many2many('stock.lot', string='Free Offcuts', compute='_compute_candidate_ids')
    lot_id = fields.Many2one('stock.lot', string='Offcut', domain="[('id', 'in', candidate_ids)]")

    @api.depends('part_id', 'job_id')
    def _compute_candidate_ids(self):
        for wizard in self:
            wizard.candidate_ids = wizard._td_candidates()

    def _td_candidates(self):
        """Free business offcuts of the same board as the part, both sides not smaller than the part (turned by 90°
        too): in stock, not reserved by anyone."""
        self.ensure_one()
        part = self.part_id
        if not part:
            return self.env['stock.lot']
        length, width = part.length_mm, part.width_mm
        lots = self.env['stock.lot'].search([
            ('td_is_offcut', '=', True), ('product_id', '=', part.material_id.id),
            ('company_id', 'in', (False, self.job_id.company_id.id))])
        quants = self.env['stock.quant'].search([
            ('lot_id', 'in', lots.ids), ('location_id.usage', '=', 'internal'), ('quantity', '>', 0)])
        in_stock = quants.lot_id
        return lots.filtered(lambda lot: lot in in_stock and float_compare(lot.td_reserved_m2, 0.0, precision_digits=4) <= 0
                             and ((lot.td_length_mm >= length and lot.td_width_mm >= width)
                                  or (lot.td_length_mm >= width and lot.td_width_mm >= length)))

    def action_reserve(self):
        """Reserve the chosen offcut on the material of the manufacturing order of the part (standard reservation by
        lot): the cutting of the job takes the reserved offcut first."""
        self.ensure_one()
        if not self.lot_id or self.lot_id not in self._td_candidates():
            raise UserError(self.env._("Choose a free offcut of the same board, not smaller than the part."))
        production = self.job_id.production_ids.filtered(lambda mo: mo.bom_id == self.part_id.bom_id)[:1]
        move = production.move_raw_ids.filtered(
            lambda m: m.product_id == self.lot_id.product_id and m.state not in ('done', 'cancel'))[:1]
        if not move:
            raise UserError(self.env._("The manufacturing order of the part does not consume %s.",
                                       self.lot_id.product_id.display_name))
        quant = self.env['stock.quant'].search([('lot_id', '=', self.lot_id.id), ('location_id', 'child_of',
                                                                                    move.location_id.id)], limit=1)
        if not quant:
            raise UserError(self.env._("Offcut %s is not in the stock of the manufacturing order.", self.lot_id.name))
        move._update_reserved_quantity(quant.quantity - quant.reserved_quantity, move.location_id, lot_id=self.lot_id,
                                       strict=True)
        self.job_id.message_post(body=self.env._("Offcut %(lot)s (%(size)s mm) reserved for part %(part)s.",
                                                 lot=self.lot_id.name, part=self.part_id.name,
                                                 size=f"{self.lot_id.td_length_mm}×{self.lot_id.td_width_mm}"))
        return {'type': 'ir.actions.act_window_close'}
