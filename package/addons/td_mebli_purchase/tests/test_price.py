from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPriceHistory(TransactionCase):

    def test_price_above_the_average_of_earlier_purchases(self):
        env = self.env
        vendor = env['res.partner'].create({'name': 'Vendor'})
        product = env['product.product'].create({'name': 'Hinge', 'type': 'consu'})
        now = fields.Datetime.now()

        def buy(price, days_ago, qty=10):
            order = env['purchase.order'].create({'partner_id': vendor.id, 'date_order': now - timedelta(days=days_ago),
                                                  'order_line': [(0, 0, {'product_id': product.id, 'product_qty': qty,
                                                                         'price_unit': price})]})
            order.button_confirm()
            order.date_order = now - timedelta(days=days_ago)
            return order.order_line

        buy(40.0, 60)
        buy(44.0, 30)
        line = buy(50.0, 1)
        self.assertAlmostEqual(line.td_history_price, 42.0)
        self.assertTrue(line.td_over_history)
        self.assertAlmostEqual(line.td_overpay, 80.0)
        old = buy(30.0, 400)
        self.assertFalse(old.td_over_history)  # no history in 180 days before it

    def test_ac_085_threshold_from_the_company(self):
        """VP-11: the threshold «price above history» is the parameter of the company (td_mebli_base), not a constant."""
        env = self.env
        vendor = env['res.partner'].create({'name': 'Vendor'})
        product = env['product.product'].create({'name': 'Handle', 'type': 'consu'})
        now = fields.Datetime.now()

        def buy(price, days_ago):
            order = env['purchase.order'].create({'partner_id': vendor.id, 'date_order': now - timedelta(days=days_ago),
                                                  'order_line': [(0, 0, {'product_id': product.id, 'product_qty': 10,
                                                                         'price_unit': price})]})
            order.button_confirm()
            order.date_order = now - timedelta(days=days_ago)
            return order.order_line

        buy(100.0, 30)
        line = buy(108.0, 1)  # +8 %
        env.company.td_price_threshold_pct = 5.0
        self.assertTrue(line.td_over_history)
        # review A-14 m1: no manual recompute — the stored mark and the filter follow the new threshold
        env.company.td_price_threshold_pct = 10.0
        self.assertFalse(line.td_over_history)
        self.assertFalse(env['purchase.order.line'].search([('td_over_history', '=', True), ('id', '=', line.id)]))
        env.company.td_price_threshold_pct = 5.0
        self.assertEqual(env['purchase.order.line'].search([('td_over_history', '=', True), ('id', '=', line.id)]), line)

    def test_ac_086_no_history_no_mark_and_a_hint(self):
        env = self.env
        vendor = env['res.partner'].create({'name': 'Vendor'})
        product = env['product.product'].create({'name': 'New hinge', 'type': 'consu'})
        order = env['purchase.order'].create({'partner_id': vendor.id, 'order_line': [
            (0, 0, {'product_id': product.id, 'product_qty': 5, 'price_unit': 70.0})]})
        line = order.order_line
        self.assertFalse(line.td_over_history)
        self.assertFalse(line.td_history_price)  # the column of the history is empty
        self.assertEqual(line.td_history_note, 'no history')
        self.assertFalse(line.td_overpay)
        order.button_confirm()  # no error

    def test_ac_085_mark_above_history_with_the_percent(self):
        env = self.env
        env.company.td_price_threshold_pct = 5.0
        vendor = env['res.partner'].create({'name': 'Vendor'})
        product = env['product.product'].create({'name': 'Drawer runner', 'type': 'consu'})
        now = fields.Datetime.now()
        old = env['purchase.order'].create({'partner_id': vendor.id, 'date_order': now - timedelta(days=20),
                                            'order_line': [(0, 0, {'product_id': product.id, 'product_qty': 10,
                                                                   'price_unit': 100.0})]})
        old.button_confirm()
        old.date_order = now - timedelta(days=20)
        line = env['purchase.order'].create({'partner_id': vendor.id, 'order_line': [
            (0, 0, {'product_id': product.id, 'product_qty': 10, 'price_unit': 108.0})]}).order_line
        self.assertTrue(line.td_over_history)
        self.assertEqual(line.td_history_note, 'Above history +8 %')
        self.assertAlmostEqual(line.td_overpay, 80.0)
        over = env['purchase.order.line'].search([('td_over_history', '=', True), ('id', '=', line.id)])
        self.assertEqual(over, line)  # the filter «Above history»

    def test_m3_other_currency_and_unit(self):
        """Review A-14 M3: the earlier purchases in EUR and by the dozen are converted into the currency of the company
        at the date of their order and into the unit of the product before the average; the average is shown in the
        currency and the unit of the new line."""
        env = self.env
        env.company.td_price_threshold_pct = 5.0
        company_currency = env.company.currency_id
        eur = env.ref('base.EUR') if company_currency != env.ref('base.EUR') else env.ref('base.USD')
        eur.active = True
        now = fields.Datetime.now()
        env['res.currency.rate'].search([('currency_id', 'in', (eur | company_currency).ids),
                                         ('company_id', 'in', (env.company.id, False))]).unlink()
        env['res.currency.rate'].create({'currency_id': eur.id, 'company_id': env.company.id, 'rate': 1 / 40.0,
                                         'name': (now - timedelta(days=90)).date()})
        env['res.currency.rate'].create({'currency_id': eur.id, 'company_id': env.company.id, 'rate': 1 / 50.0,
                                         'name': (now - timedelta(days=10)).date()})
        unit, dozen = env.ref('uom.product_uom_unit'), env.ref('uom.product_uom_dozen')
        vendor = env['res.partner'].create({'name': 'Vendor EUR'})
        product = env['product.product'].create({'name': 'Lift-up fitting', 'type': 'consu', 'uom_id': unit.id})

        def buy(price, days_ago, currency, qty, uom):
            order = env['purchase.order'].create({
                'partner_id': vendor.id, 'currency_id': currency.id, 'date_order': now - timedelta(days=days_ago),
                'order_line': [(0, 0, {'product_id': product.id, 'product_qty': qty, 'price_unit': price,
                                       'product_uom_id': uom.id})]})
            order.button_confirm()
            order.date_order = now - timedelta(days=days_ago)
            return order.order_line

        buy(1.0, 60, eur, 10, unit)             # 10 units × 1 EUR at 40 = 40 per unit
        buy(240.0, 5, company_currency, 1, dozen)   # 12 units × 20 per unit
        line = buy(36.0, 1, company_currency, 12, unit)
        # (10 × 40 + 12 × 20) / 22 = 29.0909…; a plain average of the prices (1, 240) would be meaningless
        self.assertAlmostEqual(line.td_history_price, 640.0 / 22, places=2)
        self.assertTrue(line.td_over_history)
        # a new line in EUR by the dozen (the three purchases above are its history): (400 + 240 + 432) / 34 per unit
        # in the currency of the company → × 12 per dozen, / 50 in EUR at today's rate = 7.57 EUR per dozen
        eur_line = buy(7.0, 0, eur, 1, dozen)
        self.assertAlmostEqual(eur_line.td_history_price, 1072.0 / 34 * 12 / 50, places=2)
        self.assertFalse(eur_line.td_over_history)

    def test_m3_history_of_another_company_is_not_used(self):
        """AC-036: the history is the history of the company of the line."""
        env = self.env
        other = env['res.company'].create({'name': 'Second Ltd'})
        vendor = env['res.partner'].create({'name': 'Vendor'})
        product = env['product.product'].create({'name': 'Hinge X', 'type': 'consu', 'company_id': False})
        now = fields.Datetime.now()
        order = env['purchase.order'].with_company(other).create({
            'partner_id': vendor.id, 'company_id': other.id, 'date_order': now - timedelta(days=5),
            'order_line': [(0, 0, {'product_id': product.id, 'product_qty': 10, 'price_unit': 10.0})]})
        order.button_confirm()
        order.date_order = now - timedelta(days=5)
        line = env['purchase.order'].create({'partner_id': vendor.id, 'order_line': [
            (0, 0, {'product_id': product.id, 'product_qty': 10, 'price_unit': 100.0})]}).order_line
        self.assertFalse(line.td_history_price)
        self.assertFalse(line.td_over_history)
