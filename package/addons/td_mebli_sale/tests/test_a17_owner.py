from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import TdMebliSaleCommon


@tagged('post_install', '-at_install')
class TestA17Sale(TdMebliSaleCommon):
    """A-17: the remarks of the owner 2026-11-16 in td_mebli_sale — №7 (AC-136) the size out of the limits while typing,
    №8 (AC-137) the negative margin with its reason, №9 (AC-138) one button «Print» with the list of the forms,
    №15 (D-25) one smart button «Production»."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env

        def make(login, groups):
            return env['res.users'].with_context(no_reset_password=True).create({
                'name': login, 'login': login, 'group_ids': [(6, 0, [env.ref(g).id for g in groups])]})
        cls.salesman = make('td_a17_salesman', ['sales_team.group_sale_salesman',
                                                'td_mebli_base.group_feature_configurator'])
        cls.sale_manager = make('td_a17_sale_manager', ['sales_team.group_sale_manager',
                                                        'td_mebli_base.group_feature_configurator'])
        cls.both = make('td_a17_both', ['sales_team.group_sale_salesman', 'mrp.group_mrp_user'])

    # №15 ------------------------------------------------------------------------------------------------------------
    def _form_arch(self, user):
        return self.env['sale.order'].with_user(user).get_views([(False, 'form')])['views']['form']['arch']

    def test_15_one_production_button(self):
        self.assertIn('action_td_view_production', self._form_arch(self.salesman), "salesperson: our button")
        arch = self._form_arch(self.both)
        self.assertNotIn('action_td_view_production', arch, "sales + manufacturing: the standard button only")
        self.assertIn('action_view_mrp_production', arch)

    # №7 -------------------------------------------------------------------------------------------------------------
    def test_07_warning_while_typing_every_axis(self):
        line = self._make_order().order_line
        new = line.new({'product_id': self.cabinet.id, 'td_width': 5000, 'td_height': 100, 'td_depth': 450},
                       origin=line)
        result = new._onchange_td_dims_warning()
        message = result['warning']['message']
        for text in ('5000', '400-1200', '100', '500-900'):
            self.assertIn(text, message)
        self.assertNotIn('450 mm', message, "the depth is inside the limits")
        new = line.new({'product_id': self.cabinet.id, 'td_width': 1000, 'td_height': 700, 'td_depth': 450},
                       origin=line)
        self.assertFalse(new._onchange_td_dims_warning())
        self.assertEqual(line.td_dims_range.count('-'), 3)

    def test_07_save_error_names_every_axis(self):
        with self.assertRaises(ValidationError) as error:
            self._make_order(width=5000, height=100)
        self.assertIn('5000', str(error.exception))
        self.assertIn('100', str(error.exception))

    # №8 -------------------------------------------------------------------------------------------------------------
    def test_08_negative_margin_warning_with_reason(self):
        order = self._make_order()
        order.user_id = self.salesman
        line = order.order_line
        self.assertTrue(line.sudo().purchase_price, "the planned cost of the order BoM")
        line.price_unit = line.sudo().purchase_price * 2
        self.assertFalse(line.td_below_cost)
        self.assertFalse(order.td_margin_warning)
        line.price_unit = line.sudo().purchase_price / 2
        self.assertTrue(line.td_below_cost)
        manager_text = order.with_user(self.sale_manager).td_margin_warning
        self.assertIn('%', manager_text)
        self.assertIn('nominal', manager_text)
        self.assertIn('planned cost', manager_text)
        order.invalidate_recordset(['td_margin_warning'])
        salesman_text = order.with_user(self.salesman).td_margin_warning
        self.assertTrue(salesman_text, "the salesperson sees the warning too")
        self.assertNotIn('margin', salesman_text.lower().replace('the price is below', ''),
                         "no amounts of the margin for the salesperson (AC-018)")
        order.action_confirm()  # a warning, not a block
        self.assertEqual(order.state, 'sale')

    # №9 -------------------------------------------------------------------------------------------------------------
    def test_09_print_button_with_the_list(self):
        order = self._make_order()
        order.user_id = self.salesman
        arch = self._form_arch(self.salesman)
        self.assertIn('action_td_print', arch)
        action = order.with_user(self.salesman).action_td_print()
        wizard = self.env[action['res_model']].with_user(self.salesman).browse(action['res_id'])
        reports = wizard.report_ids
        self.assertIn(self.env.ref('sale.action_report_saleorder'), reports)
        self.assertIn(self.env.ref('td_mebli_sale.action_report_contract'), reports)
        self.assertTrue(all(r.binding_model_id.model == 'sale.order' for r in reports))
        wizard.report_id = self.env.ref('td_mebli_sale.action_report_contract')
        result = wizard.action_print()
        self.assertEqual(result['type'], 'ir.actions.report')
        self.assertTrue(result['close_on_report_download'])
