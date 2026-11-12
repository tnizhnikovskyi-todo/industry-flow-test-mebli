from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestNbuRates(TransactionCase):

    def test_rates_into_the_standard_rate_table(self):
        env = self.env
        uah, eur = env.ref('base.UAH'), env.ref('base.EUR')
        uah.active = eur.active = True
        company = env['res.company'].create({'name': 'Furniture UA', 'currency_id': uah.id})
        with self.assertRaises(UserError):  # online loading is off by default: no network in the slice
            env['res.currency'].td_update_nbu_rates()
        env['res.currency'].td_update_nbu_rates({'EUR': 48.0}, imitation=True)
        rate = env['res.currency.rate'].search([('currency_id', '=', eur.id), ('company_id', '=', company.id)])
        self.assertAlmostEqual(rate.rate, 1 / 48.0)
        self.assertEqual(rate.td_source, 'nbu_imitation')
        env['res.currency'].td_update_nbu_rates({'EUR': 50.0}, imitation=True)  # the same day: updated, not doubled
        rate = env['res.currency.rate'].search([('currency_id', '=', eur.id), ('company_id', '=', company.id)])
        self.assertEqual(len(rate), 1)
        self.assertAlmostEqual(rate.rate, 1 / 50.0)
