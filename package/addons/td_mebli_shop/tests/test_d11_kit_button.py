from lxml import etree

from odoo.tests import Form, tagged

from odoo.addons.td_mebli_sale.tests.common import TdMebliSaleCommon


@tagged('post_install', '-at_install')
class TestKitButton(TdMebliSaleCommon):
    """D-11 (AC-091): the storekeeper builds the packing list in the interface — the button is in the header of the
    confirmed order and of its delivery for Inventory users (checked in the views served to the role), it builds the
    list by places and opens it; a list with packed lines is not rebuilt."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.store = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Storekeeper', 'login': 'td_d11_store', 'email': 'td_d11_store@example.com',
            'group_ids': [(6, 0, [env.ref('base.group_user').id, env.ref('stock.group_stock_user').id,
                                  env.ref('mrp.group_mrp_user').id])]})

    def _button(self, model, name, user):
        arch = self.env[model].with_user(user).get_views([(False, 'form')])['views']['form']['arch']
        return etree.fromstring(arch).xpath(f"//header/button[@name='{name}']")

    def test_d11_button_in_the_order_and_the_delivery_for_the_storekeeper(self):
        self.assertTrue(self._button('sale.order', 'action_td_form_kit', self.store), "order header, storekeeper")
        self.assertTrue(self._button('stock.picking', 'action_td_form_kit', self.store), "delivery header, storekeeper")
        salesman = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Salesman', 'login': 'td_d11_sale',
            'group_ids': [(6, 0, [self.env.ref('sales_team.group_sale_salesman').id])]})
        self.assertFalse(self._button('sale.order', 'action_td_form_kit', salesman), "not for a salesman")

    def test_d11_storekeeper_builds_the_list_from_the_order_and_the_delivery(self):
        order = self._make_order()
        order.action_confirm()
        # the form of the order as the storekeeper: the button is visible on the confirmed order without a list
        with Form(order.with_user(self.store)) as form:
            self.assertEqual(form.state, 'sale')
            self.assertFalse(form.td_kit_line_ids)
        action = order.with_user(self.store).action_td_form_kit()
        self.assertEqual(action['res_model'], 'td.mebli.kit.line')
        self.assertEqual(action['domain'], [('order_id', '=', order.id)])
        lines = order.td_kit_line_ids
        self.assertTrue(lines, "the packing list is built")
        self.assertEqual(set(lines.mapped('kind')) - {'body', 'facade', 'fitting'}, set())
        lines[:1].with_user(self.store).action_td_pack()
        # from the delivery: the list with a packed line is opened, not rebuilt (the mark stays)
        picking = order.picking_ids.filtered(lambda p: p.picking_type_code == 'outgoing')[:1]
        self.assertTrue(picking)
        action = picking.with_user(self.store).action_td_form_kit()
        self.assertEqual(action['domain'], [('order_id', '=', order.id)])
        self.assertEqual(order.td_kit_line_ids, lines)
        self.assertTrue(lines[:1].packed)
