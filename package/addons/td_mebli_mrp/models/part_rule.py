from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TdMebliPartRule(models.Model):
    _name = 'td.mebli.part.rule'
    _description = 'Furniture Part Rule'
    _order = 'product_tmpl_id, sequence, id'

    product_tmpl_id = fields.Many2one('product.template', string='Product', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Part', required=True, translate=True)
    qty = fields.Integer(string='Quantity', default=1)
    material_role = fields.Selection(
        [('body_board', 'Body board'), ('facade_board', 'Facade board'), ('fixed', 'Fixed material')],
        string='Material', required=True, default='body_board')
    fixed_material_id = fields.Many2one('product.product', string='Fixed Material')
    len_w = fields.Float(string='Length: x Width')
    len_h = fields.Float(string='Length: x Height')
    len_d = fields.Float(string='Length: x Depth')
    len_const = fields.Float(string='Length: constant, mm')
    wid_w = fields.Float(string='Width: x Width')
    wid_h = fields.Float(string='Width: x Height')
    wid_d = fields.Float(string='Width: x Depth')
    wid_const = fields.Float(string='Width: constant, mm')
    edge_long_sides = fields.Integer(string='Edged Long Sides')
    edge_short_sides = fields.Integer(string='Edged Short Sides')

    _qty_positive = models.Constraint('CHECK (qty > 0)', 'The part quantity must be positive.')
    _edge_sides_range = models.Constraint(
        'CHECK (edge_long_sides BETWEEN 0 AND 2 AND edge_short_sides BETWEEN 0 AND 2)',
        'The number of edged sides must be between 0 and 2.')

    def _compute_size(self, dims):
        """Return (length_mm, width_mm) for the given dimensions dict."""
        self.ensure_one()
        width, height, depth = dims['width'], dims['height'], dims['depth']
        length = self.len_w * width + self.len_h * height + self.len_d * depth + self.len_const
        part_width = self.wid_w * width + self.wid_h * height + self.wid_d * depth + self.wid_const
        return length, part_width

    @api.constrains('product_tmpl_id', 'len_w', 'len_h', 'len_d', 'len_const',
                    'wid_w', 'wid_h', 'wid_d', 'wid_const')
    def _check_positive_at_nominal(self):
        for rule in self:
            tmpl = rule.product_tmpl_id
            if not tmpl.td_is_parametric:
                continue
            dims = {'width': tmpl.td_width_nominal, 'height': tmpl.td_height_nominal, 'depth': tmpl.td_depth_nominal}
            length, width = rule._compute_size(dims)
            if length <= 0 or width <= 0:
                raise ValidationError(self.env._(
                    "Part %(part)s has non-positive size at nominal dimensions (%(length)s x %(width)s mm).",
                    part=rule.name, length=length, width=width))
