from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

from .common import TdMebliSaleCommon


@tagged('post_install', '-at_install')
class TestA117Sale(TdMebliSaleCommon):
    """A-11-7: the defects of A-16 in td_mebli_sale — tests through the form (Form) and the views of the role, not only
    through the model (the unit tests of A-11-6 did not see the form errors)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env

        def make(login, groups):
            return env['res.users'].with_context(no_reset_password=True).create({
                'name': login, 'login': login, 'group_ids': [(6, 0, [env.ref(g).id for g in groups])]})
        cls.salesman = make('td_a117_salesman', ['sales_team.group_sale_salesman',
                                                 'td_mebli_base.group_feature_configurator'])
        cls.sale_manager = make('td_a117_sale_manager', ['sales_team.group_sale_manager',
                                                         'td_mebli_base.group_feature_configurator'])

    # D-02 -----------------------------------------------------------------------------------------------------------
    def test_d02_salesman_saves_a_new_order_from_the_form(self):
        with Form(self.env['sale.order'].with_user(self.salesman)) as form:
            form.partner_id = self.partner
            with form.order_line.new() as line:
                line.product_id = self.cabinet
        self.assertEqual(form.record.td_stage, 'quote')

    def test_d02_the_stage_sent_back_unchanged_is_not_a_move(self):
        order = self.env['sale.order'].with_user(self.salesman).create(
            {'partner_id': self.partner.id, 'td_stage': 'quote'})
        order.write({'td_stage': 'quote'})  # a form that sends the derived stage back: nothing refused
        self.assertEqual(order.td_stage, 'quote')
        with self.assertRaises(UserError):  # a real move by a salesperson stays refused (AC-064)
            order.write({'td_stage': 'progress'})

    # D-04 / AC-015 --------------------------------------------------------------------------------------------------
    def test_d04_width_in_the_line_changes_the_price(self):
        order = self._make_order(width=1000, height=700)
        order.user_id = self.salesman  # own documents of the salesperson
        price_1000 = order.order_line.price_unit
        with Form(order.with_user(self.salesman)) as form:
            with form.order_line.edit(0) as line:
                line.td_width = 1200
                self.assertAlmostEqual(line.price_unit, price_1000 * 1.2, places=2, msg="the price in the form")
        line = order.order_line
        self.assertAlmostEqual(line.price_unit, price_1000 * 1.2, places=2)
        self.assertIn('1200', line.product_custom_attribute_value_ids.mapped('custom_value'))
        self.assertIn(f'{self.attr_w.name}: 1200', line.name)
        self.assertNotIn(f'{self.attr_w.name}: 1000', line.name)

    def test_d04_width_out_of_range_in_the_line(self):
        order = self._make_order(width=1000)
        with self.assertRaises(ValidationError):
            order.order_line.td_width = 5000

    # D-05 / AC-019 --------------------------------------------------------------------------------------------------
    def test_d05_milestones_in_the_form(self):
        term = self.env.ref('td_mebli_sale.payment_term_td_furniture')
        self.assertTrue(term.line_ids.filtered('td_milestone'))
        order = self._make_order()
        order.user_id = self.salesman
        with Form(order.with_user(self.salesman)) as form:
            form.payment_term_id = term
            self.assertTrue(form.td_pay_has_milestones)
            html = str(form.td_pay_schedule_html)
            self.assertIn('td_pay_schedule', html)
            self.assertEqual(html.count('<tr>'), len(term.line_ids))
        arch = order.with_user(self.salesman).get_views([(False, 'form')])['views']['form']['arch']
        self.assertIn('name="td_pay_schedule_html"', arch)

    # D-12 / AC-017 --------------------------------------------------------------------------------------------------
    def test_d12_cost_tab(self):
        order = self._make_order()
        arch = order.with_user(self.sale_manager).get_views([(False, 'form')])['views']['form']['arch']
        self.assertIn('name="td_cost_plan"', arch, "the tab «Cost» for the sales manager")
        self.env.company.td_margin_to_salesman = False
        self.env.registry.clear_cache()
        arch = order.with_user(self.salesman).get_views([(False, 'form')])['views']['form']['arch']
        self.assertNotIn('name="td_cost_plan"', arch, "AC-018: no cost for the salesperson without the margin")
        lines = order.with_user(self.sale_manager).td_cost_line_ids
        self.assertEqual(lines, order.order_line)
        self.assertTrue(lines.td_planned_material_cost, "planned materials of the line")
        with Form(order.with_user(self.sale_manager)) as form:
            self.assertEqual(len(form.td_cost_line_ids), 1)

    # D-13 -----------------------------------------------------------------------------------------------------------
    def test_d13_axis_in_the_language_of_the_user(self):
        self.env['res.lang']._activate_lang('uk_UA')
        order = self._make_order(width=1000)
        with self.assertRaises(ValidationError) as error:
            order.order_line.with_context(lang='uk_UA').td_width = 5000
        self.assertNotIn('width', str(error.exception))
