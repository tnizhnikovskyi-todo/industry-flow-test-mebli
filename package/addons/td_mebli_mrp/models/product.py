from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    td_is_parametric = fields.Boolean(string='Parametric Product')
    td_width_nominal = fields.Integer(string='Nominal Width, mm')
    td_height_nominal = fields.Integer(string='Nominal Height, mm')
    td_depth_nominal = fields.Integer(string='Nominal Depth, mm')
    td_width_min = fields.Integer(string='Min Width, mm')
    td_width_max = fields.Integer(string='Max Width, mm')
    td_height_min = fields.Integer(string='Min Height, mm')
    td_height_max = fields.Integer(string='Max Height, mm')
    td_depth_min = fields.Integer(string='Min Depth, mm')
    td_depth_max = fields.Integer(string='Max Depth, mm')
    td_edge_allowance_mm = fields.Integer(string='Edge Allowance, mm', default=30,
        help='Extra edge banding length added for every edged side of a part.')
    td_part_rule_ids = fields.One2many('td.mebli.part.rule', 'product_tmpl_id', string='Part Rules', copy=True)

    td_material_kind = fields.Selection(
        [('board', 'Board'), ('edge', 'Edge banding'), ('fitting', 'Fitting')],
        string='Material Kind')
    td_sheet_length_mm = fields.Integer(string='Sheet Length, mm')
    td_sheet_width_mm = fields.Integer(string='Sheet Width, mm')
    td_thickness_mm = fields.Float(string='Thickness, mm')
    td_waste_pct = fields.Float(string='Planned Waste, %', default=15.0)
    td_matches_board_id = fields.Many2one('product.product', string='Matches Board', ondelete='set null',
        help='For edge banding: the board decor this edge goes with.')
    td_edge_thickness = fields.Float(string='Edge Thickness, mm')

    _td_waste_pct_range = models.Constraint(
        'CHECK (td_waste_pct >= 0 AND td_waste_pct < 100)',
        'Planned waste must be between 0 and 100 percent.',
    )

    @api.constrains(
        'td_is_parametric', 'td_width_nominal', 'td_height_nominal', 'td_depth_nominal',
        'td_width_min', 'td_width_max', 'td_height_min', 'td_height_max', 'td_depth_min', 'td_depth_max')
    def _check_td_dimension_limits(self):
        for tmpl in self.filtered('td_is_parametric'):
            for axis in ('width', 'height', 'depth'):
                low, nominal, high = (tmpl[f'td_{axis}_min'], tmpl[f'td_{axis}_nominal'], tmpl[f'td_{axis}_max'])
                if not low <= nominal <= high:
                    raise ValidationError(self.env._(
                        "%(product)s: the %(axis)s must satisfy min <= nominal <= max (%(low)s <= %(nominal)s <= %(high)s).",
                        product=tmpl.display_name, axis=axis, low=low, nominal=nominal, high=high))


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    td_dimension = fields.Selection(
        [('width', 'Width'), ('height', 'Height'), ('depth', 'Depth')], string='Furniture Dimension')
    td_component_role = fields.Selection(
        [('body_board', 'Body board'), ('facade_board', 'Facade board'),
         ('edge', 'Edge banding'), ('fitting_set', 'Fitting set')],
        string='Component Role')


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    td_component_product_id = fields.Many2one('product.product', string='Component Product', ondelete='set null',
        help='Board or fitting set that this attribute value stands for.')
    td_edge_thickness = fields.Float(string='Edge Thickness, mm')


class ProductAttributeCustomValue(models.Model):
    _inherit = 'product.attribute.custom.value'

    @api.depends('custom_product_template_attribute_value_id.name', 'custom_value')
    def _compute_name(self):
        """A size typed by the user reads 'Width, mm: 1800' (not 'Width, mm: Enter size: 1800')."""
        super()._compute_name()
        for record in self:
            attribute = record.custom_product_template_attribute_value_id.attribute_id
            if attribute.td_dimension:
                record.name = f'{attribute.name}: {(record.custom_value or "").strip()}'
