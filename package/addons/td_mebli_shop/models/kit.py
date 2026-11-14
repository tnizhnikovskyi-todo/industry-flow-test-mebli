from odoo import api, fields, models
from odoo.exceptions import UserError

KIND_PLACE = {'body': 0, 'facade': 1, 'fitting': 2}


class TdMebliKitLine(models.Model):
    _name = 'td.mebli.kit.line'
    _description = 'Packing List Line'
    _order = 'order_id, place, sequence, id'

    order_id = fields.Many2one('sale.order', string='Order', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    place = fields.Integer(string='Place', required=True, default=1)
    kind = fields.Selection([('body', 'Body'), ('facade', 'Fronts'), ('fitting', 'Fittings')], string='Kind',
                            required=True, default='body')
    item = fields.Char(string='Item', required=True)
    part_id = fields.Many2one('td.mebli.part', string='Part', ondelete='set null')
    qty = fields.Float(string='Quantity', default=1.0, digits=(16, 2))
    label = fields.Char(string='Label', compute='_compute_label')
    packed = fields.Boolean(string='Packed')
    packed_by_id = fields.Many2one('res.users', string='Packed by', readonly=True)
    company_id = fields.Many2one(related='order_id.company_id', store=True, string='Company')
    # AC-093: «Create additional order» — a manufacturing order of the missing part, linked to the sales order
    reorder_production_id = fields.Many2one('mrp.production', string='Reordered', readonly=True, copy=False)

    @api.depends('order_id.name', 'place', 'sequence')
    def _compute_label(self):
        for line in self:
            line.label = f"{line.order_id.name}-{line.place}-{line.sequence:02d}"

    def write(self, vals):
        if 'packed' in vals:
            vals['packed_by_id'] = self.env.uid if vals['packed'] else False
        return super().write(vals)

    def action_td_pack(self):
        self.write({'packed': True})
        return True

    def action_td_reorder(self):
        """AC-093: the part is missing in the set — a manufacturing order of the part with the sales order as origin; the
        line is marked «Reordered»."""
        for line in self:
            if not line.part_id:
                raise UserError(self.env._("An additional order is made for a part: %s is not a part.", line.item))
            if line.reorder_production_id:
                raise UserError(self.env._("%(item)s is already reordered: %(production)s.",
                                           item=line.item, production=line.reorder_production_id.name))
            production = line.part_id._td_make_production(
                line.qty, line.order_id.name,
                self.env._("Additional order of %(item)s for %(order)s (packing list).",
                           item=line.item, order=line.order_id.name))
            line.reorder_production_id = production
            line.order_id.message_post(body=self.env._("Additional order of %(item)s: %(production)s.",
                                                       item=line.item, production=production.name))
        return True


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    td_kit_line_ids = fields.One2many('td.mebli.kit.line', 'order_id', string='Packing List')
    td_kit_missing = fields.Integer(string='Not Packed', compute='_compute_td_kit')
    td_kit_places = fields.Integer(string='Places', compute='_compute_td_kit')

    @api.depends('td_kit_line_ids.packed', 'td_kit_line_ids.place')
    def _compute_td_kit(self):
        for order in self:
            order.td_kit_missing = len(order.td_kit_line_ids.filtered(lambda line: not line.packed))
            order.td_kit_places = len(set(order.td_kit_line_ids.mapped('place')))

    def action_td_build_kit(self):
        """Packing list from the order bills of materials: body parts, fronts and fittings, each kind in its places."""
        Line = self.env['td.mebli.kit.line']
        for order in self:
            order.td_kit_line_ids.unlink()
            vals, base = [], 0
            for sale_line in order.order_line.filtered('td_bom_id'):
                bom = sale_line.td_bom_id
                seq = {k: 0 for k in KIND_PLACE}
                product = sale_line.product_id.product_tmpl_id.name
                for part in bom.td_part_ids:
                    kind = 'facade' if part.rule_id.material_role == 'facade_board' else 'body'
                    seq[kind] += 1
                    vals.append({'order_id': order.id, 'place': base + KIND_PLACE[kind] + 1, 'kind': kind,
                                 'sequence': seq[kind], 'item': f"{product}: {part.name}", 'part_id': part.id,
                                 'qty': part.qty * sale_line.product_uom_qty})
                for bom_line in bom.bom_line_ids.filtered(
                        lambda line: line.product_id.td_material_kind in ('fitting', 'facade')):
                    kind = 'fitting' if bom_line.product_id.td_material_kind == 'fitting' else 'facade'
                    seq[kind] += 1
                    vals.append({'order_id': order.id, 'place': base + KIND_PLACE[kind] + 1, 'kind': kind,
                                 'sequence': seq[kind], 'item': f"{product}: {bom_line.product_id.name}",
                                 'qty': bom_line.product_qty * sale_line.product_uom_qty})
                base += len(KIND_PLACE)
            Line.create(vals)
        return True

    def action_td_form_kit(self):
        """D-11 (AC-091): the button «Build the Packing List» of the order (or of its delivery) for the warehouse: the
        list is built from the order bills of materials and opened by place. A list with packed lines is not rebuilt
        (the marks «packed» stay): the button only opens it."""
        self.ensure_one()
        if not self.order_line.filtered('td_bom_id'):
            raise UserError(self.env._(
                "The order %s has no bill of materials of a product yet: the packing list is built from the bills of "
                "materials of the order lines.", self.name))
        if not self.td_kit_line_ids.filtered('packed'):
            self.action_td_build_kit()
        return self.action_td_view_kit()

    def _td_kit_by_place(self):
        """The packing list grouped by place, for the printed list: [(place, lines)]."""
        self.ensure_one()
        places = sorted(set(self.td_kit_line_ids.mapped('place')))
        return [(place, self.td_kit_line_ids.filtered(lambda line: line.place == place)) for place in places]

    def action_td_scan_labels(self):
        """AC-062: scanning of the part labels into the packing list (box B)."""
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'res_model': 'td.mebli.kit.scan', 'view_mode': 'form', 'target': 'new',
                'name': self.env._("Scan Labels"), 'context': {'default_order_id': self.id}}

    def action_td_view_kit(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('td_mebli_shop.td_mebli_kit_line_action')
        action['domain'] = [('order_id', '=', self.id)]
        action['context'] = {'default_order_id': self.id, 'search_default_group_place': 1}
        action['name'] = self.env._("Packing List %s", self.name)
        return action


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_td_form_kit(self):
        """D-11 (AC-091): the same button on the delivery of the order."""
        self.ensure_one()
        if not self.sale_id:
            raise UserError(self.env._("The transfer %s has no sales order: there is nothing to pack.", self.name))
        return self.sale_id.action_td_form_kit()

    def button_validate(self):
        for picking in self.filtered(lambda p: p.picking_type_code == 'outgoing' and p.sale_id):
            missing = picking.sale_id.td_kit_line_ids.filtered(lambda line: not line.packed)
            if missing:
                places = sorted(set(missing.mapped('place')))
                raise UserError(self.env._(
                    "The set of order %(order)s is incomplete: %(count)s items are not packed (places %(places)s), "
                    "for example «%(item)s». An incomplete set does not leave the warehouse.",
                    order=picking.sale_id.name, count=len(missing), places=', '.join(map(str, places)),
                    item=missing[0].item))
        return super().button_validate()
