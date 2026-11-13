from datetime import timedelta
from unittest.mock import patch

import requests

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestNbuRates(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.uah, cls.eur = env.ref('base.UAH'), env.ref('base.EUR')
        (cls.uah | cls.eur).active = True
        cls.company = env['res.company'].create({'name': 'Furniture UA', 'currency_id': cls.uah.id})
        cls.finance = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Finance UA', 'login': 'td_ua_finance', 'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'group_ids': [(6, 0, [env.ref('base.group_user').id, env.ref('td_mebli_base.group_finance').id,
                                  env.ref('sales_team.group_sale_salesman_all_leads').id])]})

    def _rate(self):
        return self.env['res.currency.rate'].search([('currency_id', '=', self.eur.id), ('company_id', '=', self.company.id)])

    def test_rates_into_the_standard_rate_table(self):
        env = self.env
        with self.assertRaises(UserError):  # online loading is off by default: no network in the slice
            env['res.currency'].td_update_nbu_rates()
        env['res.currency'].td_update_nbu_rates({'EUR': 48.0}, imitation=True)
        rate = self._rate()
        self.assertAlmostEqual(rate.rate, 1 / 48.0)
        self.assertEqual(rate.td_source, 'nbu_imitation')
        env['res.currency'].td_update_nbu_rates({'EUR': 50.0}, imitation=True)  # the same day: updated, not doubled
        rate = self._rate()
        self.assertEqual(len(rate), 1)
        self.assertAlmostEqual(rate.rate, 1 / 50.0)

    def test_ac_037_cron_writes_the_nbu_source(self):
        """AC-037: the daily job loads the rate (the NBU service is a mock, no network) with the source «NBU»."""
        self.env['ir.config_parameter'].sudo().set_param('td_mebli_ua.nbu_online', '1')
        with patch.object(type(self.env['res.currency']), '_td_fetch_nbu', return_value={'EUR': 49.5}):
            self.assertTrue(self.env['res.currency']._td_cron_nbu())
        rate = self._rate()
        self.assertEqual(rate.td_source, 'nbu')
        self.assertAlmostEqual(rate.rate, 1 / 49.5)

    def test_ac_037_update_prices_only_quotations(self):
        """AC-037: «Update Prices at the Rate» recomputes the quotations from the EUR price list at the new rate; the
        confirmed order keeps its prices; the chatter of the quotation has the old and the new total."""
        env = self.env
        Rate = env['res.currency.rate']
        Rate.create({'currency_id': self.eur.id, 'company_id': self.company.id, 'rate': 1 / 40.0,
                     'name': fields.Date.today() - timedelta(days=3)})
        eur_list = env['product.pricelist'].create({
            'name': 'Fittings EUR', 'currency_id': self.eur.id, 'company_id': self.company.id,
            'item_ids': [(0, 0, {'applied_on': '3_global', 'compute_price': 'fixed', 'fixed_price': 10.0})]})
        uah_list = env['product.pricelist'].create({
            'name': 'Retail UAH', 'currency_id': self.uah.id, 'company_id': self.company.id,
            'item_ids': [(0, 0, {'applied_on': '3_global', 'base': 'pricelist', 'base_pricelist_id': eur_list.id,
                                 'compute_price': 'formula'})]})
        hinge = env['product.product'].create({'name': 'Hinge', 'list_price': 1.0, 'taxes_id': [(5, 0, 0)]})
        partner = env['res.partner'].create({'name': 'Customer UA'})

        def order():
            return env['sale.order'].with_company(self.company).create({
                'partner_id': partner.id, 'pricelist_id': uah_list.id, 'company_id': self.company.id,
                'order_line': [(0, 0, {'product_id': hinge.id, 'product_uom_qty': 10})]})
        quotation, confirmed = order(), order()
        self.assertAlmostEqual(quotation.amount_untaxed, 4000.0)
        confirmed.action_confirm()
        env['res.currency'].td_update_nbu_rates({'EUR': 50.0})
        result = env['sale.order'].with_user(self.finance).with_company(self.company).td_action_update_prices_by_rate()
        self.assertEqual(result['tag'], 'display_notification')
        self.assertAlmostEqual(quotation.amount_untaxed, 5000.0)
        self.assertAlmostEqual(confirmed.amount_untaxed, 4000.0, msg="a confirmed order is not changed")
        body = quotation.message_ids[0].body
        self.assertRegex(body, r'4(&nbsp;|[\s\xa0,])000', "the old total is in the chatter")
        self.assertRegex(body, r'5(&nbsp;|[\s\xa0,])000', "the new total is in the chatter")

    def _eur_quotation_setup(self):
        env = self.env
        env['res.currency.rate'].create({'currency_id': self.eur.id, 'company_id': self.company.id, 'rate': 1 / 40.0,
                                         'name': fields.Date.today() - timedelta(days=3)})
        eur_list = env['product.pricelist'].create({
            'name': 'Fittings EUR', 'currency_id': self.eur.id, 'company_id': self.company.id,
            'item_ids': [(0, 0, {'applied_on': '3_global', 'compute_price': 'fixed', 'fixed_price': 10.0})]})
        uah_list = env['product.pricelist'].create({
            'name': 'Retail UAH', 'currency_id': self.uah.id, 'company_id': self.company.id,
            'item_ids': [(0, 0, {'applied_on': '3_global', 'base': 'pricelist', 'base_pricelist_id': eur_list.id,
                                 'compute_price': 'formula'})]})
        hinge = env['product.product'].create({'name': 'Hinge', 'list_price': 1.0, 'taxes_id': [(5, 0, 0)]})
        partner = env['res.partner'].create({'name': 'Customer UA'})
        return env['sale.order'].with_company(self.company).create({
            'partner_id': partner.id, 'pricelist_id': uah_list.id, 'company_id': self.company.id,
            'date_order': fields.Datetime.now() - timedelta(days=2),
            'order_line': [(0, 0, {'product_id': hinge.id, 'product_uom_qty': 10}),
                           (0, 0, {'product_id': hinge.id, 'product_uom_qty': 10}),
                           (0, 0, {'product_id': hinge.id, 'product_uom_qty': 10})]})

    def test_ac_037_manual_price_discount_and_date_kept(self):
        """Review A-14 M1: the rate update recomputes only the lines priced by the price list; the unit price and the
        discount typed by the salesperson stay, the date of the quotation is not changed."""
        quotation = self._eur_quotation_setup()
        auto, manual_price, manual_discount = quotation.order_line
        self.assertAlmostEqual(auto.price_unit, 400.0)
        manual_price.price_unit = 350.0
        manual_discount.discount = 10.0
        date_order = quotation.date_order
        self.env['res.currency'].td_update_nbu_rates({'EUR': 50.0})
        result = self.env['sale.order'].with_user(self.finance).with_company(self.company) \
            .td_action_update_prices_by_rate()
        self.assertAlmostEqual(auto.price_unit, 500.0, msg="the line of the price list gets today's rate")
        self.assertAlmostEqual(manual_price.price_unit, 350.0, msg="the manual price stays")
        self.assertAlmostEqual((manual_discount.price_unit, manual_discount.discount), (400.0, 10.0),
                               msg="the manual discount stays, its line is not recomputed")
        self.assertEqual(quotation.date_order, date_order, "the date of the quotation is not changed")
        kept = self.env['sale.order'].with_user(self.finance).env._("Lines with a manual price or discount kept: %(count)s.", count=2)
        self.assertIn(kept, result['params']['message'])
        self.assertIn(kept, quotation.message_ids[0].body)

    def test_ac_037_other_company_not_touched(self):
        """The quotations of a company not selected by the finance user stay as they are."""
        quotation = self._eur_quotation_setup()
        other = self.env['res.company'].create({'name': 'Second UA', 'currency_id': self.uah.id})
        self.finance.company_ids = [(4, other.id)]
        self.env['res.currency'].td_update_nbu_rates({'EUR': 50.0})
        self.env['sale.order'].with_user(self.finance).with_company(other).td_action_update_prices_by_rate()
        self.assertAlmostEqual(quotation.order_line[0].price_unit, 400.0)

    def test_security_5_public_rate_writer_only_for_the_administrator(self):
        """Review A-14 security 5: an accounting manager cannot write rates marked «NBU» through the public method."""
        manager = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Accountant UA', 'login': 'td_ua_accountant', 'company_id': self.company.id,
            'company_ids': [(6, 0, [self.company.id])],
            'group_ids': [(6, 0, [self.env.ref('account.group_account_manager').id,
                                  self.env.ref('td_mebli_base.group_finance').id])]})
        with self.assertRaises(AccessError):
            self.env['res.currency'].with_user(manager).td_update_nbu_rates({'EUR': 1.0})
        self.assertFalse(self._rate())

    def test_ac_037_update_prices_needs_finance(self):
        salesman = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Salesman UA', 'login': 'td_ua_salesman',
            'group_ids': [(6, 0, [self.env.ref('sales_team.group_sale_salesman').id])]})
        with self.assertRaises(AccessError):
            self.env['sale.order'].with_user(salesman).td_action_update_prices_by_rate()

    def test_ac_037_menu_behind_the_feature_group(self):
        menu = self.env.ref('td_mebli_ua.menu_td_update_prices_by_rate')
        self.assertEqual(menu.group_ids, self.env.ref('td_mebli_base.group_feature_nbu'))

    def test_ac_038_nbu_down_keeps_rates_and_warns_finance(self):
        """AC-038: the NBU service fails → the rates are not changed, an error in the log, the finance user gets the
        activity «NBU rate not updated» (only one for repeated failures); the job stays scheduled."""
        env = self.env
        env['res.currency'].td_update_nbu_rates({'EUR': 48.0})
        env['ir.config_parameter'].sudo().set_param('td_mebli_ua.nbu_online', '1')
        Currency = type(env['res.currency'])
        for error in (requests.ConnectionError('timeout'), ValueError('bad json')):
            with patch.object(Currency, '_td_fetch_nbu', side_effect=error), \
                    self.assertLogs('odoo.addons.td_mebli_ua.models.currency', level='ERROR'):
                self.assertFalse(env['res.currency']._td_cron_nbu())
        self.assertAlmostEqual(self._rate().rate, 1 / 48.0, msg="the rates are not changed")
        activities = env['mail.activity'].search([('res_model', '=', 'res.partner'),
                                                  ('res_id', '=', self.company.partner_id.id),
                                                  ('user_id', '=', self.finance.id)])
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities.summary, 'NBU rate not updated')
        cron = env.ref('td_mebli_ua.ir_cron_td_nbu_rates')
        self.assertEqual((cron.interval_number, cron.interval_type), (1, 'days'))

    def test_ac_038_fetch_rejects_a_broken_answer(self):
        """The format check of the NBU answer (mock of the HTTP answer): an empty list is an error, not «no rates»."""
        answer = type('Answer', (), {'raise_for_status': lambda self: None, 'json': lambda self: []})()
        with patch('odoo.addons.td_mebli_ua.models.currency.requests.get', return_value=answer):
            with self.assertRaises(ValueError):
                self.env['res.currency']._td_fetch_nbu()

    def test_ac_038_uk_texts(self):
        """The Ukrainian texts of SPEC: the activity «Курс НБУ не оновлено»."""
        from odoo.tools.misc import file_path
        with open(file_path('td_mebli_ua/i18n/uk.po'), encoding='utf-8') as po:
            self.assertIn('msgstr "Курс НБУ не оновлено"', po.read())
