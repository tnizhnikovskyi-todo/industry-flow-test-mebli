from odoo import models

PART_FIELDS = ('sequence', 'name', 'material_id', 'length_mm', 'width_mm', 'edge_long_sides', 'edge_short_sides',
               'edge_product_id')


class TdMebliPart(models.Model):
    _inherit = 'td.mebli.part'

    def _td_make_production(self, qty, origin, note):
        """A manufacturing order for this part only: a repeat part after a scrap (AC-073) or an additional order of a
        missing part (AC-093). The product is the service-like «Repeat part» of the package; the bill of materials is a
        one-part specification (board and edge banding from the part), so the cutting and the costs see it like any
        order. Created by the system: the kiosk and the packer have no manufacturing rights of their own."""
        self.ensure_one()
        product = self.env.ref('td_mebli_shop.product_td_repeat_part')
        company = self.bom_id.company_id or self.env.company
        vals = {field: self[field].id if hasattr(self[field], 'id') else self[field] for field in PART_FIELDS}
        vals['qty'] = max(int(qty or 1), 1)
        # sudo: a repeat part needs a BoM of one part; the manufacturing user only reads BoMs
        Bom = self.env['mrp.bom'].sudo().with_company(company)
        bom = Bom.create({
            'product_tmpl_id': product.product_tmpl_id.id, 'product_id': product.id, 'product_qty': 1.0,
            'type': 'normal', 'company_id': company.id, 'td_order_bom': True, 'consumption': 'warning',
            'code': f"{origin}: {self.name}", 'td_part_ids': [(0, 0, vals)]})
        bom._td_recompute_component_lines()
        # sudo: the repeat part is a system order from the tablet / claim, in the company of the source order
        production = self.env['mrp.production'].sudo().with_company(company).create({
            'product_id': product.id, 'product_qty': 1.0, 'product_uom_id': product.uom_id.id, 'bom_id': bom.id,
            'origin': origin, 'company_id': company.id})
        production.action_confirm()
        production.message_post(body=note)
        return production
