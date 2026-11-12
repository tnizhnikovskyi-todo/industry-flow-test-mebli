from collections import defaultdict

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Domain


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    td_order_bom = fields.Boolean(string='Order BoM', readonly=True, copy=False, index=True)
    td_template_bom_id = fields.Many2one('mrp.bom', string='Template BoM', readonly=True, copy=False,
                                         ondelete='set null')
    td_width = fields.Integer(string='Width, mm', readonly=True, copy=False)
    td_height = fields.Integer(string='Height, mm', readonly=True, copy=False)
    td_depth = fields.Integer(string='Depth, mm', readonly=True, copy=False)
    td_part_ids = fields.One2many('td.mebli.part', 'bom_id', string='Parts', copy=False)
    td_part_count = fields.Integer(string='Part Count', compute='_compute_td_totals')
    td_board_area_m2 = fields.Float(string='Board Area, m2', compute='_compute_td_totals', digits=(16, 3))
    td_edge_length_m = fields.Float(string='Edge, m', compute='_compute_td_totals', digits=(16, 3))

    @api.depends('td_part_ids.qty', 'td_part_ids.area_m2', 'td_part_ids.edge_length_m')
    def _compute_td_totals(self):
        for bom in self:
            bom.td_part_count = sum(bom.td_part_ids.mapped('qty'))
            bom.td_board_area_m2 = sum(bom.td_part_ids.mapped('area_m2'))
            bom.td_edge_length_m = sum(bom.td_part_ids.mapped('edge_length_m'))

    @api.model
    def _bom_find_domain(self, products, picking_type=None, company_id=False, bom_type=False):
        domain = super()._bom_find_domain(
            products, picking_type=picking_type, company_id=company_id, bom_type=bom_type)
        return domain & Domain('td_order_bom', '=', False)

    # ------------------------------------------------------------------
    # Order BoM generator
    # ------------------------------------------------------------------
    @api.model
    def _td_pick_components(self, selections):
        """Split the chosen attribute values by component role."""
        picked = {'body_board': False, 'facade_board': False, 'edge_thickness': 0.0, 'fittings': self.env['product.product']}
        for value in selections:
            role = value.attribute_id.td_component_role
            if role in ('body_board', 'facade_board'):
                picked[role] = value.td_component_product_id
            elif role == 'edge':
                picked['edge_thickness'] = value.td_edge_thickness
            elif role == 'fitting_set' and value.td_component_product_id:
                picked['fittings'] |= value.td_component_product_id
        return picked

    @api.model
    def _td_find_edge(self, board, thickness):
        """Edge banding of the exact thickness; without thickness (facades) the thickest one for the board."""
        domain = [('td_material_kind', '=', 'edge'), ('td_matches_board_id', '=', board.id)]
        if thickness:
            domain.append(('td_edge_thickness', '=', thickness))
        edge = self.env['product.product'].search(domain, order='td_edge_thickness desc, id', limit=1)
        if not edge:
            raise UserError(self.env._(
                "No edge banding %(thickness)s mm found for %(board)s.",
                thickness=thickness, board=board.display_name))
        return edge

    @api.model
    def _td_generate_order_bom(self, product, dims, selections):
        """Create a bill of materials for one concrete order.

        :param product: product.product (parametric)
        :param dims: dict width/height/depth in mm
        :param selections: product.attribute.value recordset chosen by the customer
        """
        tmpl = product.product_tmpl_id
        if not tmpl.td_is_parametric:
            raise UserError(self.env._("%s is not a parametric product.", product.display_name))
        for axis in ('width', 'height', 'depth'):
            low, high = tmpl[f'td_{axis}_min'], tmpl[f'td_{axis}_max']
            if not low <= dims[axis] <= high:
                raise UserError(self.env._(
                    "%(axis)s %(value)s mm is out of range %(low)s-%(high)s mm.",
                    axis=axis, value=dims[axis], low=low, high=high))
        template_bom = self._bom_find(product)[product]
        template_lines = template_bom._td_applicable_lines(product, selections)
        # ready-made fronts (painted MDF) are bought by a line of the template: the facade parts are not cut, else they
        # would be counted twice (board under cutting + bought fronts)
        bought_facade = bool(template_lines.filtered(lambda line: line.product_id.td_material_kind == 'facade'))
        picked = self._td_pick_components(selections)
        if not picked['body_board']:
            raise UserError(self.env._("Choose a body decor for %s.", product.display_name))
        facade = picked['facade_board'] or picked['body_board']

        part_vals = []
        for rule in tmpl.td_part_rule_ids:
            if bought_facade and rule.material_role == 'facade_board':
                continue
            if rule.material_role == 'fixed':
                material = rule.fixed_material_id
            elif rule.material_role == 'facade_board':
                material = facade
            else:
                material = picked['body_board']
            if not material:
                raise UserError(self.env._("Part %s has no material.", rule.name))
            length, width = rule._compute_size(dims)
            if length <= 0 or width <= 0:
                raise UserError(self.env._("Part %s has a non-positive size.", rule.name))
            edge = self.env['product.product']
            if rule.edge_long_sides or rule.edge_short_sides:
                thickness = 0.0 if rule.material_role == 'facade_board' else picked['edge_thickness']
                edge = self._td_find_edge(material, thickness)
            part_vals.append({
                'rule_id': rule.id, 'sequence': rule.sequence, 'name': rule.name,
                'material_id': material.id, 'qty': rule.qty,
                'length_mm': length, 'width_mm': width,
                'edge_long_sides': rule.edge_long_sides, 'edge_short_sides': rule.edge_short_sides,
                'edge_product_id': edge.id,
            })

        bom = self.create({
            'product_tmpl_id': tmpl.id,
            'product_id': product.id,
            'product_qty': 1.0,
            'product_uom_id': template_bom.product_uom_id.id or tmpl.uom_id.id,
            'type': 'normal',
            'code': self.env._("%(w)sx%(h)sx%(d)s order BoM", w=dims['width'], h=dims['height'], d=dims['depth']),
            'td_order_bom': True,
            'td_template_bom_id': template_bom.id,
            # standard lead times of the template: the end of the manufacturing order follows from them
            'produce_delay': template_bom.produce_delay,
            'days_to_prepare_mo': template_bom.days_to_prepare_mo,
            'td_width': dims['width'], 'td_height': dims['height'], 'td_depth': dims['depth'],
            'td_part_ids': [(0, 0, vals) for vals in part_vals],
        })
        bom.write({
            'bom_line_ids': bom._td_prepare_component_lines(template_lines, picked),
        })
        bom.write({
            'operation_ids': bom._td_prepare_operations(template_bom),
        })
        return bom

    def _td_applicable_lines(self, product, selections):
        """Lines of the template BoM that apply to the chosen attribute values (standard «Apply on Variants»,
        mrp.bom.line._skip_bom_line; the furniture attributes are no_variant, so the values are passed as never values)."""
        if not self:
            return self.env['mrp.bom.line']
        self.ensure_one()
        chosen = self.product_tmpl_id.attribute_line_ids.product_template_value_ids.filtered(
            lambda ptav: ptav.product_attribute_value_id in selections)
        return self.bom_line_ids.filtered(lambda line: not line._skip_bom_line(product, never_attribute_values=chosen))

    def _td_prepare_component_lines(self, template_lines, picked):
        self.ensure_one()
        uom_m2 = self.env.ref('uom.product_uom_square_meter')
        uom_m = self.env.ref('uom.product_uom_meter')
        area = defaultdict(float)
        edge = defaultdict(float)
        for part in self.td_part_ids:
            area[part.material_id] += part.area_m2
            if part.edge_product_id:
                edge[part.edge_product_id] += part.edge_length_m
        lines = []
        for board, square_meters in area.items():
            waste = board.td_waste_pct
            lines.append((0, 0, {
                'product_id': board.id,
                'product_qty': round(square_meters * (1 + waste / 100.0), 4),
                'product_uom_id': uom_m2.id,
            }))
        for product, metres in edge.items():
            lines.append((0, 0, {
                'product_id': product.id, 'product_qty': round(metres, 3), 'product_uom_id': uom_m.id,
            }))
        for fitting in picked['fittings']:
            lines.append((0, 0, {'product_id': fitting.id, 'product_qty': 1.0, 'product_uom_id': fitting.uom_id.id}))
        for line in template_lines:
            lines.append((0, 0, {
                'product_id': line.product_id.id, 'product_qty': line.product_qty,
                'product_uom_id': line.product_uom_id.id,
            }))
        return lines

    def _td_prepare_operations(self, template_bom):
        self.ensure_one()
        quantities = {
            'per_part': self.td_part_count,
            'per_edge_m': self.td_edge_length_m,
            'per_board_m2': self.td_board_area_m2,
        }
        operations = []
        for op in template_bom.operation_ids:
            duration = op.time_cycle_manual
            if op.td_time_basis != 'fixed':
                duration = op.td_time_rate * quantities[op.td_time_basis]
            operations.append((0, 0, {
                'name': op.name, 'workcenter_id': op.workcenter_id.id, 'sequence': op.sequence,
                'time_mode': 'manual', 'time_cycle_manual': duration,
                'td_time_basis': op.td_time_basis, 'td_time_rate': op.td_time_rate,
                'td_piece_rate': op.td_piece_rate,
            }))
        return operations
