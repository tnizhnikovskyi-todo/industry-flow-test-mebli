from collections import defaultdict

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Domain
from odoo.tools import float_compare


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
    # AC-052 / AC-028: number of the version sent to cutting; 0 — not sent. Set by the system (td_mebli_cutting) when the
    # parts go to cutting or to the distributor; while > 0 the parts are locked (td.mebli.part._td_check_not_sent)
    td_cut_version = fields.Integer(string='Cutting Version', readonly=True, copy=False, default=0,
                                    help="Version of the specification sent to cutting. 0 — not sent yet. Once sent, the "
                                         "parts are changed only by an additional order.")

    @api.depends('td_part_ids.qty', 'td_part_ids.area_m2', 'td_part_ids.edge_length_m')
    def _compute_td_totals(self):
        for bom in self:
            bom.td_part_count = sum(bom.td_part_ids.mapped('qty'))
            bom.td_board_area_m2 = sum(bom.td_part_ids.mapped('area_m2'))
            bom.td_edge_length_m = sum(bom.td_part_ids.mapped('edge_length_m'))

    def _td_mark_sent_to_cutting(self):
        """Called by the cutting (system): the next version of every specification is sent; returns {bom: version}."""
        versions = {}
        # sudo: called by the cutting (system): the version of the sent specification is written whoever sends
        for bom in self.sudo():
            bom.td_cut_version += 1
            versions[bom.id] = bom.td_cut_version
        return versions

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
            # position 3: overconsumption of the materials of an order is shown before the order is closed (standard
            # «Flexible Consumption: Allowed with warning», mrp.consumption.warning)
            'consumption': 'warning',
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

    def _td_part_quantities(self):
        """Board (m2, with the planned waste) and edge banding (m) needed by the parts: {product: quantity}."""
        self.ensure_one()
        area = defaultdict(float)
        edge = defaultdict(float)
        for part in self.td_part_ids:
            area[part.material_id] += part.area_m2
            if part.edge_product_id:
                edge[part.edge_product_id] += part.edge_length_m
        quantities = {board: round(square_meters * (1 + board.td_waste_pct / 100.0), 4)
                      for board, square_meters in area.items()}
        quantities.update({product: round(metres, 3) for product, metres in edge.items()})
        return quantities

    def _td_prepare_component_lines(self, template_lines, picked):
        self.ensure_one()
        uom_m2 = self.env.ref('uom.product_uom_square_meter')
        uom_m = self.env.ref('uom.product_uom_meter')
        lines = []
        for product, qty in self._td_part_quantities().items():
            lines.append((0, 0, {
                'product_id': product.id, 'product_qty': qty,
                'product_uom_id': (uom_m if product.td_material_kind == 'edge' else uom_m2).id,
            }))
        for fitting in picked['fittings']:
            lines.append((0, 0, {'product_id': fitting.id, 'product_qty': 1.0, 'product_uom_id': fitting.uom_id.id}))
        for line in template_lines:
            lines.append((0, 0, {
                'product_id': line.product_id.id, 'product_qty': line.product_qty,
                'product_uom_id': line.product_uom_id.id,
            }))
        return lines

    def _td_recompute_component_lines(self):
        """AC-045: after an import the board and edge banding lines are the quantities the parts need (marked «From
        parts»); fittings and the other lines stay as they are."""
        uom_m2 = self.env.ref('uom.product_uom_square_meter')
        uom_m = self.env.ref('uom.product_uom_meter')
        for bom in self:
            commands = [(2, line.id) for line in bom.bom_line_ids
                        if line.product_id.td_material_kind in ('board', 'edge')]
            commands += [(0, 0, {'product_id': product.id, 'product_qty': qty,
                                 'product_uom_id': (uom_m if product.td_material_kind == 'edge' else uom_m2).id})
                         for product, qty in bom._td_part_quantities().items()]
            bom.write({'bom_line_ids': commands})

    def action_td_import_parts(self):
        """Button «Import parts» of the specification (hidden once the specification is sent to cutting)."""
        self.ensure_one()
        self.env['td.mebli.part']._td_check_not_sent(self)
        action = self.env['ir.actions.act_window']._for_xml_id('td_mebli_mrp.td_mebli_spec_import_action')
        action['context'] = {'default_bom_id': self.id}
        return action

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


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    # read only marker: the quantity of a board or an edge banding line of a bill of materials with parts is the sum of
    # the parts (area plus planned waste, edge length) — see MrpBom._td_prepare_component_lines; nothing is entered here
    td_from_parts = fields.Boolean(
        string='From Parts', compute='_compute_td_from_parts',
        help="Read only: the quantity of this board or edge banding is calculated from the parts of the bill of "
             "materials (tab Parts): area of the parts plus the planned waste, length of the edged sides. Not marked "
             "when the quantity differs from what the parts need.")

    @api.depends('product_id.td_material_kind', 'product_id.td_waste_pct', 'product_qty', 'product_uom_id',
                 'bom_id.td_part_ids.material_id', 'bom_id.td_part_ids.edge_product_id',
                 'bom_id.td_part_ids.area_m2', 'bom_id.td_part_ids.edge_length_m')
    def _compute_td_from_parts(self):
        """Marked when the line is a board or an edge banding of the parts AND its quantity is the one the parts need
        (a line edited by hand, or parts added later without recalculation, is not marked)."""
        uom_m2 = self.env.ref('uom.product_uom_square_meter')
        uom_m = self.env.ref('uom.product_uom_meter')
        needed_by_bom = {}
        for line in self:
            line.td_from_parts = False
            bom = line.bom_id
            kind = line.product_id.td_material_kind
            if not bom.td_part_ids or kind not in ('board', 'edge'):
                continue
            if bom not in needed_by_bom:
                needed_by_bom[bom] = bom._td_part_quantities()
            needed = needed_by_bom[bom].get(line.product_id)
            if needed is None:
                continue
            uom = uom_m if kind == 'edge' else uom_m2
            qty = line.product_uom_id._compute_quantity(line.product_qty, uom) if line.product_uom_id else line.product_qty
            line.td_from_parts = float_compare(qty, needed, precision_digits=3) == 0
