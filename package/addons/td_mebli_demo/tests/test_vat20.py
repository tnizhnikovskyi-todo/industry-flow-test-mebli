from odoo.tests import TransactionCase, tagged

from odoo.addons.td_mebli_demo.showcase import _vat20


@tagged('post_install', '-at_install')
class TestDemoVat20(TransactionCase):
    """D-01 (A-15 спроба 2): the demo seed takes the 20 % VAT of the chart and never renames or changes the chart taxes."""

    def test_chart_taxes_untouched_and_reused(self):
        Tax = self.env['account.tax'].with_context(active_test=False)
        before = {t.id: (t.name, t.amount) for t in Tax.search([])}
        # a chart with several taxes (as ua_psbo): one more 20 % sale tax and a 7 % one must keep their names and rates
        extra = Tax.create({'name': 'Test 7%', 'amount': 7.0, 'amount_type': 'percent', 'type_tax_use': 'sale'})
        sale, purchase = _vat20(self.env)
        self.assertEqual((sale.amount, sale.type_tax_use), (20.0, 'sale'))
        self.assertEqual((purchase.amount, purchase.type_tax_use), (20.0, 'purchase'))
        for tax in Tax.browse(list(before)):
            self.assertEqual((tax.name, tax.amount), before[tax.id])
        self.assertEqual((extra.name, extra.amount), ('Test 7%', 7.0))
        self.assertEqual(self.env.company.account_sale_tax_id, sale)
        self.assertEqual(self.env.company.account_purchase_tax_id, purchase)
        wardrobe = self.env.ref('td_mebli_demo.prod_wardrobe')
        self.assertIn(wardrobe.taxes_id, (sale, wardrobe.taxes_id.browse()))

    def test_idempotent(self):
        first = _vat20(self.env)
        count = self.env['account.tax'].search_count([])
        self.assertEqual(_vat20(self.env), first)
        self.assertEqual(self.env['account.tax'].search_count([]), count)
