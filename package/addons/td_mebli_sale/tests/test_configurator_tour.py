from odoo.tests import HttpCase, tagged

from .common import TdMebliSaleCommon


@tagged('post_install', '-at_install')
class TestConfiguratorTour(HttpCase, TdMebliSaleCommon):
    """D-02 / D-04 / D-15 (A-11-7): the salesperson of the showroom creates the order in the form, configures the
    cabinet, SAVES it, then changes the width in the line and saves again. The tour starts from the action of the
    quotations (not from the start menu of «Sales», which on the full profile opens the measurement sheets) and its user
    works in Ukrainian when the language is installed (the tour selectors do not read the texts of the interface)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        groups = [cls.env.ref('sales_team.group_sale_salesman'), cls.env.ref('td_mebli_base.group_feature_configurator')]
        uk = cls.env['res.lang']._lang_get('uk_UA')
        cls.salon = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Showroom manager', 'login': 'td_tour_salon', 'password': 'td_tour_salon',
            'group_ids': [(6, 0, [group.id for group in groups])],
            'lang': 'uk_UA' if uk and uk.active else 'en_US'})

    def test_configurator_dimensions(self):
        self.start_tour('/odoo/action-sale.action_quotations_with_onboarding', 'td_mebli_sale_configurator_tour',
                        login='td_tour_salon')
        order = self.env['sale.order'].search([('partner_id', '=', self.partner.id), ('user_id', '=', self.salon.id)])
        self.assertEqual(len(order), 1, "D-02: the new order is saved from the form")
        self.assertEqual(order.td_stage, 'quote')
        line = order.order_line.filtered(lambda l: l.product_id == self.cabinet)
        self.assertEqual((line.td_width, line.td_height, line.td_depth), (1200, 700, 500))
        self.assertEqual(sorted(line.product_custom_attribute_value_ids.mapped('custom_value')), ['1200', '500', '700'],
                         "D-04: the width of the line goes back to the value of the configurator")
        self.assertAlmostEqual(line.td_size_factor, (1200 * 700) / (800 * 700), places=3)
        reference = self._make_order(width=1000).order_line
        self.assertAlmostEqual(line.price_unit, reference.price_unit * 1.2, places=2,
                               msg="AC-015: the width typed in the line changes the price")
