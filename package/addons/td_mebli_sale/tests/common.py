from odoo.addons.td_mebli_mrp.tests.common import TdMebliCommon


class TdMebliSaleCommon(TdMebliCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        # price extras on the choice values
        cls.val_b.default_extra_price = 600.0
        cls.val_e2.default_extra_price = 350.0
        cls.attr_w, (cls.val_w,) = cls._dimension_attribute('Width, mm', 'width')
        cls.attr_h, (cls.val_h,) = cls._dimension_attribute('Height, mm', 'height')
        cls.attr_d, (cls.val_d,) = cls._dimension_attribute('Depth, mm', 'depth')
        attributes = [cls.attr_body, cls.attr_facade, cls.attr_edge, cls.attr_fit, cls.attr_w, cls.attr_h, cls.attr_d]
        cls.cabinet_tmpl.write({'attribute_line_ids': [
            (0, 0, {'attribute_id': attr.id, 'value_ids': [(6, 0, attr.value_ids.ids)]}) for attr in attributes]})
        cls.cabinet_tmpl.invalidate_recordset()
        cls.ptav = {
            ptav.product_attribute_value_id: ptav
            for ptav in cls.cabinet_tmpl.attribute_line_ids.product_template_value_ids}
        cls.cabinet = cls.cabinet_tmpl.product_variant_id
        mto = env.ref('stock.route_warehouse0_mto')
        mto.active = True
        cls.cabinet_tmpl.route_ids = [(6, 0, [env.ref('mrp.route_warehouse0_manufacture').id, mto.id])]
        cls.partner = env['res.partner'].create({'name': 'Test customer'})

    @classmethod
    def _dimension_attribute(cls, name, axis):
        attr = cls.env['product.attribute'].create({
            'name': name, 'create_variant': 'no_variant', 'td_dimension': axis,
            'value_ids': [(0, 0, {'name': 'Custom', 'is_custom': True})]})
        return attr, attr.value_ids

    @classmethod
    def _make_order(cls, width=1000, height=700, depth=500, body=None, edge=None, raw=None):
        body = body or cls.val_a
        edge = edge or cls.val_e04
        custom = []
        for value, text in ((cls.val_w, width), (cls.val_h, height), (cls.val_d, depth)):
            custom.append((0, 0, {
                'custom_product_template_attribute_value_id': cls.ptav[value].id,
                'custom_value': str(raw.get(value, text)) if raw else str(text)}))
        chosen = [cls.ptav[value].id for value in (body, cls.val_f, edge, cls.val_fit)]
        return cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.cabinet.id, 'product_uom_qty': 1.0,
                'product_custom_attribute_value_ids': custom,
                'product_no_variant_attribute_value_ids': [(6, 0, chosen)],
            })],
        })
