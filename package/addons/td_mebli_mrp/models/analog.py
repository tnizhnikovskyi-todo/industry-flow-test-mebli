from odoo import api, fields, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # position 14 (F-57, box B): analogs of a board or a decor that the technologist accepts as a replacement
    td_analog_ids = fields.Many2many(
        'product.product', 'td_mebli_product_analog_rel', 'tmpl_id', 'product_id', string='Analogs',
        help="Materials that can replace this one when it is short (same thickness and use, another decor or brand). "
             "The manufacturing order suggests the first analog that is free in stock.")


class StockMove(models.Model):
    _inherit = 'stock.move'

    td_analog_id = fields.Many2one('product.product', string='Analog in Stock', compute='_compute_td_analog')
    td_analog_hint = fields.Char(string='Analog', compute='_compute_td_analog')

    @api.depends('product_id', 'product_uom_qty', 'forecast_availability', 'state')
    def _compute_td_analog(self):
        for move in self:
            move.td_analog_id = False
            move.td_analog_hint = False
            if not move.raw_material_production_id or move.state in ('done', 'cancel') or not move.product_uom_qty:
                continue
            short = move.product_qty - (move.forecast_availability or 0.0)
            analogs = move.product_id.product_tmpl_id.td_analog_ids
            if short <= 0 or not analogs:
                continue
            free = [(p, p.with_context(location=move.location_id.id).free_qty) for p in analogs]
            enough = [(p, qty) for p, qty in free if qty >= move.product_qty]
            if enough:
                product, qty = enough[0]
                move.td_analog_id = product
                move.td_analog_hint = self.env._("%(name)s: %(qty)s free", name=product.name,
                                                 qty='%g' % round(qty, 2))

    def action_td_use_analog(self):
        """Replace the short component by its analog in the manufacturing order: the standard way of a confirmed order
        (a new component line, the old one to zero); the parts of the order BoM that were cut from it take the analog."""
        for move in self:
            analog = move.td_analog_id
            production = move.raw_material_production_id
            if not analog or not production:
                raise UserError(self.env._("No analog of %s is free in stock.", move.product_id.name))
            production.write({'move_raw_ids': [(0, 0, {
                'product_id': analog.id, 'product_uom_qty': move.product_uom_qty, 'product_uom': analog.uom_id.id,
                'location_id': move.location_id.id, 'location_dest_id': move.location_dest_id.id,
                'raw_material_production_id': production.id, 'company_id': move.company_id.id,
            })]})
            old = move.product_id
            move.product_uom_qty = 0.0
            if production.bom_id.td_order_bom:
                production.bom_id.td_part_ids.filtered(lambda part: part.material_id == old).material_id = analog
            production.message_post(body=self.env._("Component %(old)s is short: replaced by the analog %(new)s.",
                                                    old=old.name, new=analog.name))
        return True
