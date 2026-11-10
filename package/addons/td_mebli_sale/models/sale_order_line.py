from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

AXES = ('width', 'height', 'depth')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    td_is_parametric = fields.Boolean(related='product_id.product_tmpl_id.td_is_parametric')
    td_width = fields.Integer(string='Width, mm', compute='_compute_td_dims', store=True, readonly=False, precompute=True)
    td_height = fields.Integer(string='Height, mm', compute='_compute_td_dims', store=True, readonly=False, precompute=True)
    td_depth = fields.Integer(string='Depth, mm', compute='_compute_td_dims', store=True, readonly=False, precompute=True)
    td_size_factor = fields.Float(string='Size Factor', compute='_compute_td_size_factor', store=True,
                                  precompute=True, digits=(16, 3))
    td_bom_id = fields.Many2one('mrp.bom', string='Order BoM', copy=False, index='btree_not_null',
                                ondelete='set null')
    td_planned_material_cost = fields.Monetary(string='Planned Materials', compute='_compute_td_planned_cost',
                                               store=True, currency_field='currency_id')
    td_planned_operation_cost = fields.Monetary(string='Planned Operations', compute='_compute_td_planned_cost',
                                                store=True, currency_field='currency_id')

    # ------------------------------------------------------------------
    # Dimensions
    # ------------------------------------------------------------------
    def _td_read_custom_dims(self):
        """Dimensions typed in the configurator: {axis: raw string}."""
        self.ensure_one()
        raw = {}
        for custom in self.product_custom_attribute_value_ids:
            axis = custom.custom_product_template_attribute_value_id.attribute_id.td_dimension
            if axis:
                raw[axis] = (custom.custom_value or '').strip()
        return raw

    def _td_get_dims(self):
        """Dimensions in mm computed from the configurator values (nominal when not typed)."""
        self.ensure_one()
        tmpl = self.product_id.product_tmpl_id
        raw = self._td_read_custom_dims()
        dims = {}
        for axis in AXES:
            try:
                dims[axis] = int(raw[axis]) if axis in raw else tmpl[f'td_{axis}_nominal']
            except ValueError:
                dims[axis] = 0
        return dims

    @api.depends('product_id', 'product_custom_attribute_value_ids.custom_value')
    def _compute_td_dims(self):
        for line in self:
            if not line.td_is_parametric:
                line.td_width = line.td_height = line.td_depth = 0
                continue
            dims = line._td_get_dims()
            line.td_width, line.td_height, line.td_depth = (dims[axis] for axis in AXES)

    @api.constrains('product_id', 'product_custom_attribute_value_ids', 'td_width', 'td_height', 'td_depth')
    def _check_td_dims(self):
        for line in self.filtered('td_is_parametric'):
            tmpl = line.product_id.product_tmpl_id
            for axis, raw in line._td_read_custom_dims().items():
                if not raw.isdigit():
                    raise ValidationError(self.env._(
                        "%(product)s: the %(axis)s must be a whole number of millimetres, got '%(raw)s'.",
                        product=tmpl.display_name, axis=axis, raw=raw))
            for axis in AXES:
                value = line[f'td_{axis}']
                low, high = tmpl[f'td_{axis}_min'], tmpl[f'td_{axis}_max']
                if not low <= value <= high:
                    raise ValidationError(self.env._(
                        "%(product)s: the %(axis)s %(value)s mm is out of range %(low)s-%(high)s mm.",
                        product=tmpl.display_name, axis=axis, value=value, low=low, high=high))

    def _td_size_factor_for(self, width, height):
        tmpl = self.product_id.product_tmpl_id
        nominal = tmpl.td_width_nominal * tmpl.td_height_nominal
        return (width * height) / nominal if nominal else 1.0

    @api.depends('product_id', 'td_width', 'td_height')
    def _compute_td_size_factor(self):
        for line in self:
            line.td_size_factor = line._td_size_factor_for(line.td_width, line.td_height) if line.td_is_parametric else 1.0

    # ------------------------------------------------------------------
    # Price
    # ------------------------------------------------------------------
    @api.depends('td_size_factor')
    def _compute_price_unit(self):
        return super()._compute_price_unit()

    def _get_display_price(self):
        price = super()._get_display_price()
        if self.td_is_parametric:
            dims = self._td_get_dims()
            price *= self._td_size_factor_for(dims['width'], dims['height'])
        return price

    # ------------------------------------------------------------------
    # Order BoM
    # ------------------------------------------------------------------
    def _td_selections(self):
        self.ensure_one()
        return self.product_no_variant_attribute_value_ids.product_attribute_value_id | \
            self.product_id.product_template_attribute_value_ids.product_attribute_value_id

    def _td_generate_bom(self):
        """(Re)create the order BoM of the line; a BoM that already has manufacturing orders is kept."""
        Bom = self.env['mrp.bom']
        for line in self.filtered('td_is_parametric'):
            old = line.td_bom_id
            if old and self.env['mrp.production'].search_count([('bom_id', '=', old.id)], limit=1):
                continue
            dims = {axis: line[f'td_{axis}'] for axis in AXES}
            bom = Bom._td_generate_order_bom(line.product_id, dims, line._td_selections())
            bom.write({
                'td_sale_line_id': line.id,
                'code': f'{line.order_id.name or ""}/{line.id or ""} {dims["width"]}x{dims["height"]}x{dims["depth"]}',
            })
            line.td_bom_id = bom
            old.unlink()

    def action_td_generate_bom(self):
        if any(line.state not in ('draft', 'sent') for line in self):
            raise UserError(self.env._("The specification can be rebuilt only in a quotation."))
        self._td_generate_bom()
        if len(self) == 1:
            return self.action_td_open_bom()

    def action_td_open_bom(self):
        self.ensure_one()
        if not self.td_bom_id:
            raise UserError(self.env._("Generate the specification first."))
        return {
            'type': 'ir.actions.act_window', 'res_model': 'mrp.bom', 'res_id': self.td_bom_id.id,
            'view_mode': 'form', 'target': 'current',
        }

    def _action_launch_stock_rule(self, *, previous_product_uom_qty=False):
        self.filtered(lambda line: line.state == 'sale')._td_generate_bom()
        return super()._action_launch_stock_rule(previous_product_uom_qty=previous_product_uom_qty)

    def _prepare_procurement_values(self):
        values = super()._prepare_procurement_values()
        if self.td_bom_id:
            values['bom_id'] = self.td_bom_id
        return values

    # ------------------------------------------------------------------
    # Planned cost and margin
    # ------------------------------------------------------------------
    def _td_bom_unit_costs(self):
        """(materials, operations) of one unit of the product, in company currency."""
        self.ensure_one()
        bom = self.td_bom_id
        materials = sum(
            line.product_id.uom_id._compute_price(line.product_id.standard_price, line.product_uom_id) * line.product_qty
            for line in bom.bom_line_ids)
        operations = sum(bom.operation_ids.mapped('cost'))
        factor = 1.0 / (bom.product_qty or 1.0)
        return materials * factor, operations * factor

    @api.depends('td_bom_id.bom_line_ids.product_qty', 'td_bom_id.bom_line_ids.product_id.standard_price',
                 'td_bom_id.operation_ids.time_cycle_manual', 'td_bom_id.operation_ids.workcenter_id.costs_hour',
                 'product_uom_qty', 'currency_id')
    def _compute_td_planned_cost(self):
        for line in self:
            if not line.td_bom_id:
                line.td_planned_material_cost = line.td_planned_operation_cost = 0.0
                continue
            line = line.with_company(line.company_id)
            materials, operations = line._td_bom_unit_costs()
            currency = line.company_id.currency_id
            line.td_planned_material_cost = line._convert_to_sol_currency(materials, currency) * line.product_uom_qty
            line.td_planned_operation_cost = line._convert_to_sol_currency(operations, currency) * line.product_uom_qty

    @api.depends('td_bom_id', 'td_bom_id.bom_line_ids.product_qty', 'td_bom_id.operation_ids.time_cycle_manual')
    def _compute_purchase_price(self):
        super()._compute_purchase_price()
        for line in self.filtered('td_bom_id'):
            line = line.with_company(line.company_id)
            materials, operations = line._td_bom_unit_costs()
            cost = line.product_id.uom_id._compute_price(materials + operations, line.product_uom_id)
            line.purchase_price = line._convert_to_sol_currency(cost, line.company_id.currency_id)
