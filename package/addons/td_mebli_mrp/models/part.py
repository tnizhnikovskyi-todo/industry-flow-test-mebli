from odoo import api, fields, models
from odoo.exceptions import UserError


class TdMebliPart(models.Model):
    _name = 'td.mebli.part'
    _description = 'Furniture Part of an Order BoM'
    _order = 'bom_id, sequence, id'

    bom_id = fields.Many2one('mrp.bom', string='Bill of Materials', required=True, ondelete='cascade', index=True)
    rule_id = fields.Many2one('td.mebli.part.rule', string='Rule', ondelete='set null')
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Part', required=True)
    material_id = fields.Many2one('product.product', string='Material', required=True)
    qty = fields.Integer(string='Quantity', default=1)
    length_mm = fields.Float(string='Length, mm')
    width_mm = fields.Float(string='Width, mm')
    edge_long_sides = fields.Integer(string='Edged Long Sides')
    edge_short_sides = fields.Integer(string='Edged Short Sides')
    edge_product_id = fields.Many2one('product.product', string='Edge Banding')
    area_m2 = fields.Float(string='Area, m2', compute='_compute_area_m2', store=True, digits=(16, 4))
    edge_length_m = fields.Float(string='Edge, m', compute='_compute_edge_length_m', store=True, digits=(16, 3))
    # AC-052: the specification went to cutting (own cutting or the distributor, td_mebli_cutting sets the version)
    locked = fields.Boolean(string='Sent to Cutting', compute='_compute_locked')

    @api.depends('bom_id.td_cut_version')
    def _compute_locked(self):
        for part in self:
            part.locked = bool(part.bom_id.td_cut_version)

    def _td_check_not_sent(self, boms=None):
        """AC-052: parts of a specification sent to cutting are not changed — a change is a new additional order."""
        if self.env.context.get('td_cut_unlock'):
            return
        sent = (boms if boms is not None else self.bom_id).filtered('td_cut_version')
        if sent:
            raise UserError(self.env._(
                "The specification was sent to cutting (version %s) — change only by an additional order.",
                max(sent.mapped('td_cut_version'))))

    @api.model_create_multi
    def create(self, vals_list):
        boms = self.env['mrp.bom'].browse({vals['bom_id'] for vals in vals_list if vals.get('bom_id')})
        self._td_check_not_sent(boms)
        return super().create(vals_list)

    def write(self, vals):
        self._td_check_not_sent()
        if vals.get('bom_id'):
            self._td_check_not_sent(self.env['mrp.bom'].browse(vals['bom_id']))
        return super().write(vals)

    def unlink(self):
        self._td_check_not_sent()
        return super().unlink()

    @api.depends('qty', 'length_mm', 'width_mm')
    def _compute_area_m2(self):
        for part in self:
            part.area_m2 = part.qty * part.length_mm * part.width_mm / 1_000_000.0

    @api.depends('qty', 'length_mm', 'width_mm', 'edge_long_sides', 'edge_short_sides',
                 'bom_id.product_tmpl_id.td_edge_allowance_mm')
    def _compute_edge_length_m(self):
        for part in self:
            allowance = part.bom_id.product_tmpl_id.td_edge_allowance_mm
            sides = part.edge_long_sides + part.edge_short_sides
            raw = part.edge_long_sides * part.length_mm + part.edge_short_sides * part.width_mm
            part.edge_length_m = part.qty * (raw + sides * allowance) / 1000.0
