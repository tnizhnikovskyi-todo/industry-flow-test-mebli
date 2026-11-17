from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang

AXES = ('width', 'height', 'depth')
# AC-018 (tr/security.md §4): cost and margin are seen by the sales manager, the finance and the salesperson only when the
# company lets him (td_mebli_base.group_margin_view follows «The salesperson sees the margin»)
MARGIN_GROUPS = 'td_mebli_base.group_margin_view,td_mebli_base.group_finance,sales_team.group_sale_manager'


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    td_is_parametric = fields.Boolean(related='product_id.product_tmpl_id.td_is_parametric')
    td_width = fields.Integer(string='Width, mm', compute='_compute_td_dims', inverse='_inverse_td_dims', store=True,
                           readonly=False, precompute=True)
    td_height = fields.Integer(string='Height, mm', compute='_compute_td_dims', inverse='_inverse_td_dims', store=True,
                           readonly=False, precompute=True)
    td_depth = fields.Integer(string='Depth, mm', compute='_compute_td_dims', inverse='_inverse_td_dims', store=True,
                           readonly=False, precompute=True)
    td_size_factor = fields.Float(string='Size Factor', compute='_compute_td_size_factor', store=True,
                                  precompute=True, digits=(16, 3))
    td_dims_range = fields.Char(string='Size Limits, mm', compute='_compute_td_dims_range',
                                help="The width, height and depth allowed for the product.")
    # A-17 №8: the price of the line is below its planned cost (decoration of the line, the warning of the quotation)
    td_below_cost = fields.Boolean(string='Below Cost', compute='_compute_td_below_cost')
    td_bom_id = fields.Many2one('mrp.bom', string='Order BoM', copy=False, index='btree_not_null',
                                ondelete='set null')
    td_planned_material_cost = fields.Monetary(string='Planned Materials', compute='_compute_td_planned_cost',
                                               store=True, currency_field='currency_id', groups=MARGIN_GROUPS)
    td_planned_operation_cost = fields.Monetary(string='Planned Operations', compute='_compute_td_planned_cost',
                                                store=True, currency_field='currency_id', groups=MARGIN_GROUPS)
    # standard sale_margin fields (groups="base.group_user" there): the same groups as the planned cost
    margin = fields.Float(groups=MARGIN_GROUPS)
    margin_percent = fields.Float(groups=MARGIN_GROUPS)
    purchase_price = fields.Float(groups=MARGIN_GROUPS)

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

    def _inverse_td_dims(self):
        """D-04 / AC-015: a size typed in the line goes back to the value of the configurator, so that the description,
        the specification and the price follow the same size."""
        for line in self.filtered('td_is_parametric'):
            for custom in line.product_custom_attribute_value_ids:
                axis = custom.custom_product_template_attribute_value_id.attribute_id.td_dimension
                if axis and (custom.custom_value or '').strip() != str(line[f'td_{axis}']):
                    old_label = custom.name
                    custom.custom_value = str(line[f'td_{axis}'])
                    # the description of the line (printed in the quotation) reads the new size too
                    if old_label and line.name and old_label in line.name:
                        line.name = line.name.replace(old_label, custom.name)

    def _td_axis_label(self, axis):
        """D-13: the axis in the language of the user (the selection of product.attribute.td_dimension)."""
        labels = dict(self.env['product.attribute']._fields['td_dimension']._description_selection(self.env))
        return (labels.get(axis) or axis).lower()

    def _td_out_of_range(self):
        """A-17 №7: every axis of the line outside the limits of the product: [(axis, value, low, high)]."""
        self.ensure_one()
        if not self.td_is_parametric:
            return []
        tmpl = self.product_id.product_tmpl_id
        out = []
        for axis in AXES:
            value = self[f'td_{axis}']
            low, high = tmpl[f'td_{axis}_min'], tmpl[f'td_{axis}_max']
            if not low <= value <= high:
                out.append((axis, value, low, high))
        return out

    def _td_out_of_range_text(self, out):
        """«width 111 mm (allowed 800-2060 mm), height 111 mm (allowed 2000-2700 mm)» — all the axes at once."""
        return ', '.join(self.env._("%(axis)s %(value)s mm (allowed %(low)s-%(high)s mm)", axis=self._td_axis_label(axis),
                                    value=value, low=low, high=high) for axis, value, low, high in out)

    @api.depends('product_id')
    @api.depends_context('lang')
    def _compute_td_dims_range(self):
        """A-17 №7: the limits of the product next to the size columns, short: «W 800–2060 · H 2000–2700 · D 450–700»."""
        for line in self:
            tmpl = line.product_id.product_tmpl_id
            if not line.td_is_parametric:
                line.td_dims_range = False
                continue
            short = {'width': self.env._("W"), 'height': self.env._("H"), 'depth': self.env._("D")}
            line.td_dims_range = ' · '.join(
                f"{short[axis]} {tmpl[f'td_{axis}_min']}–{tmpl[f'td_{axis}_max']}" for axis in AXES)

    @api.onchange('product_id', 'product_custom_attribute_value_ids', 'td_width', 'td_height', 'td_depth')
    def _onchange_td_dims_warning(self):
        """A-17 №7: the size out of the limits is shown while the size is typed (the line, the configurator), not only
        when the quotation is saved; every wrong axis with its limits. The constraint below still blocks the save."""
        if not self.td_is_parametric:
            return None
        bad = [axis for axis, raw in self._td_read_custom_dims().items() if raw and not raw.isdigit()]
        out = self._td_out_of_range()
        if not out and not bad:
            return None
        parts = []
        if bad:
            parts.append(self.env._("not a whole number of millimetres: %s",
                                    ', '.join(self._td_axis_label(axis) for axis in bad)))
        if out:
            parts.append(self._td_out_of_range_text(out))
        return {'warning': {
            'title': self.env._("The size is out of the limits of the product"),
            'message': self.env._("%(product)s: %(problems)s. The price and the specification follow the typed size; "
                                  "the quotation is not saved until the size is corrected.",
                                  product=self.product_id.product_tmpl_id.display_name, problems='; '.join(parts)),
        }}

    @api.constrains('product_id', 'product_custom_attribute_value_ids', 'td_width', 'td_height', 'td_depth')
    def _check_td_dims(self):
        for line in self.filtered('td_is_parametric'):
            tmpl = line.product_id.product_tmpl_id
            for axis, raw in line._td_read_custom_dims().items():
                if not raw.isdigit():
                    raise ValidationError(self.env._(
                        "%(product)s: the %(axis)s must be a whole number of millimetres, got '%(raw)s'.",
                        product=tmpl.display_name, axis=line._td_axis_label(axis), raw=raw))
            out = line._td_out_of_range()
            if out:
                # A-17 №7: every axis out of the limits at once, with the limits
                raise ValidationError(self.env._(
                    "%(product)s: the size is out of the limits: %(problems)s.",
                    product=tmpl.display_name, problems=line._td_out_of_range_text(out)))

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

    def _td_is_install(self):
        """The installation service: a service that creates a task in a project (standard sale_project service_tracking;
        read by name so that td_mebli_sale does not depend on sale_project)."""
        self.ensure_one()
        product = self.product_id
        return bool(product.type == 'service' and 'service_tracking' in product._fields
                    and product.service_tracking not in (False, 'no'))

    def _get_display_price(self):
        # AC-043, VP-16: «installation in the price of the order» — the line of the installation costs nothing
        if self.order_id.company_id.td_install_in_price and self._td_is_install():
            return 0.0
        price = super()._get_display_price()
        if self.td_is_parametric:
            # D-04 / AC-015: the size of the line (typed in the line or in the configurator), not only the configurator
            price *= self._td_size_factor_for(self.td_width, self.td_height)
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
        # sudo: a salesperson has no manufacturing rights: the order specification is built and replaced as the system
        Bom = self.env['mrp.bom'].sudo()
        for line in self.filtered('td_is_parametric'):
            # sudo: the old specification is read and replaced as the system (no manufacturing rights of the salesperson)
            old = line.td_bom_id.sudo()
            # sudo: read only — is the old specification used by a manufacturing order
            if old and self.env['mrp.production'].sudo().search_count([('bom_id', '=', old.id)], limit=1):
                continue
            dims = {axis: line[f'td_{axis}'] for axis in AXES}
            bom = Bom._td_generate_order_bom(line.product_id, dims, line._td_selections())
            bom.write({
                'td_sale_line_id': line.id,
                'code': f'{line.order_id.name or ""}/{line.id or ""} {dims["width"]}x{dims["height"]}x{dims["depth"]}',
            })
            line.td_bom_id = bom
            old.unlink()

    # the specification (and so the planned cost and the margin) is built as soon as the line is saved in a quotation
    _TD_BOM_TRIGGERS = {'product_id', 'td_width', 'td_height', 'td_depth', 'product_uom_qty',
                        'product_no_variant_attribute_value_ids', 'product_custom_attribute_value_ids'}

    def _td_refresh_draft_bom(self):
        # a quotation is saved even when the specification cannot be built yet (e.g. no edge banding for the board):
        # the error then appears on confirmation, as before
        for line in self.filtered(lambda l: l.td_is_parametric and l.state in ('draft', 'sent') and l.order_id):
            try:
                with self.env.cr.savepoint():
                    line._td_generate_bom()
            except UserError:
                pass

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._td_refresh_draft_bom()
        return lines

    def write(self, vals):
        result = super().write(vals)
        if self._TD_BOM_TRIGGERS & set(vals):
            self._td_refresh_draft_bom()
        return result

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
            line.purchase_price = line.currency_id.round(line._convert_to_sol_currency(cost, line.company_id.currency_id))

    # ------------------------------------------------------------------
    # A-17 №8: negative margin — a warning with the reason
    # ------------------------------------------------------------------
    @api.depends('price_subtotal', 'product_uom_qty', 'td_bom_id', 'purchase_price')
    def _compute_td_below_cost(self):
        for line in self:
            # sudo: read only — the planned cost is hidden from a salesperson without the margin rights (AC-018); he sees
            # only that the price is below it
            data = line.sudo()
            line.td_below_cost = bool(not line.display_type and data.purchase_price and data.product_uom_qty
                                      and data.price_subtotal < data.purchase_price * data.product_uom_qty - 0.005)

    def _td_cost_split(self):
        """(does not depend on the size, follows the size, names of the parts that do not depend on the size) of one
        unit, company currency: fittings and the fixed / per-part operations against the boards, the edge banding and
        the operations by m2 of board or by metre of edge."""
        self.ensure_one()
        # sudo: read only — the order BoM (a salesperson has no manufacturing rights)
        bom = self.sudo().td_bom_id
        fixed = sized = 0.0
        fixed_names = []
        for bom_line in bom.bom_line_ids:
            cost = bom_line.product_id.uom_id._compute_price(bom_line.product_id.standard_price,
                                                             bom_line.product_uom_id) * bom_line.product_qty
            if bom_line.td_from_parts:
                sized += cost
            else:
                fixed += cost
                fixed_names.append(bom_line.product_id.name)
        for operation in bom.operation_ids:
            if operation.td_time_basis in ('per_edge_m', 'per_board_m2'):
                sized += operation.cost
            else:
                fixed += operation.cost
                fixed_names.append(operation.name)
        factor = 1.0 / (bom.product_qty or 1.0)
        return fixed * factor, sized * factor, list(dict.fromkeys(fixed_names))

    def _td_below_cost_text(self, with_amounts):
        """The reason of the negative margin of the line, in the words of the salesperson (A-17 №8)."""
        self.ensure_one()
        _ = self.env._
        line = self.sudo()  # read only: the planned cost (AC-018 hides it from a salesperson without the margin rights)
        name = line.product_id.product_tmpl_id.display_name
        parts = []
        if line.td_is_parametric:
            tmpl = line.product_id.product_tmpl_id
            parts.append(_("%(product)s %(w)s × %(h)s × %(d)s mm: the price is below the planned cost. The price is "
                           "%(pct)s %% of the base price: the size %(w)s × %(h)s mm against the nominal %(wn)s × %(hn)s mm "
                           "(the depth does not change the price).",
                           product=name, w=line.td_width, h=line.td_height, d=line.td_depth,
                           pct=round(line.td_size_factor * 100), wn=tmpl.td_width_nominal, hn=tmpl.td_height_nominal))
        else:
            parts.append(_("%(product)s: the price is below the planned cost.", product=name))
        currency = line.currency_id

        def money(value):
            # the format of the language of the user (uk_UA: «13 480,00 ₴»), as the amounts in the interface
            return formatLang(self.env, value, currency_obj=currency)
        # the price of the line was changed by hand or discounted: say it, it is often the reason
        if line.discount:
            parts.append(_("Discount %(discount)s %%.", discount=round(line.discount, 1)))
        if line.technical_price_unit and line.currency_id.compare_amounts(line.price_unit, line.technical_price_unit):
            parts.append(_("The unit price was changed by hand: %(price)s instead of %(computed)s.",
                           price=money(line.price_unit), computed=money(line.technical_price_unit)))
        fixed = sized = 0.0
        names = []
        if line.td_bom_id:
            fixed, sized, names = line._td_cost_split()
            if names:
                parts.append(_("Do not get cheaper with a smaller size: %(names)s; boards, edge banding and their "
                               "operations follow the size.", names=', '.join(names[:6])))
        if with_amounts:
            cost = line.purchase_price * line.product_uom_qty
            margin = line.price_subtotal - cost
            pct = (margin / line.price_subtotal * 100.0) if line.price_subtotal else 0.0
            amounts = _("Price %(price)s, planned cost %(cost)s, margin %(margin)s (%(pct)s %%).",
                        price=money(line.price_subtotal), cost=money(cost), margin=money(margin), pct=round(pct, 1))
            if line.td_bom_id:
                qty = line.product_uom_qty
                amounts += ' ' + _("Of the cost, not depending on the size: %(fixed)s, following the size: %(sized)s.",
                                   fixed=money(line._convert_to_sol_currency(fixed, line.company_id.currency_id) * qty),
                                   sized=money(line._convert_to_sol_currency(sized, line.company_id.currency_id) * qty))
            parts.append(amounts)
        return ' '.join(parts)
