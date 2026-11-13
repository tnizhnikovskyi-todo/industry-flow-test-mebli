import csv
import os
import tempfile

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.td_mebli_migration.scripts import convert_bas, convert_bazis, convert_core


@tagged('post_install', '-at_install')
class TestMigrationConverters(AccountTestInvoicingCommon):
    """AC-089: the converters are skeletons (formats ВП-1, ВП-3 unknown); the core maps an export into A-13 templates."""

    def _write(self, path, rows, delimiter=','):
        with open(path, 'w', encoding='utf-8', newline='') as handle:
            csv.writer(handle, delimiter=delimiter).writerows(rows)

    def test_ac_089_bas_converter_keeps_the_bas_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, templates, out = (os.path.join(tmp, name) for name in ('src', 'tpl', 'out'))
            for folder in (source, templates, out):
                os.mkdir(folder)
            # the header of the A-13 template (package/master-data/02_res.partner.csv), not its rows
            self._write(os.path.join(templates, '02_res.partner.csv'),
                        [['id', 'name', 'is_company', 'supplier_rank', 'customer_rank', 'vat', 'company_registry']])
            self._write(os.path.join(source, 'partners.csv'),
                        [['Код', 'Наименование', 'ИНН', 'ЕДРПОУ'], ['00-001', 'Демо-Постачальник', '', '1'],
                         ['00-002', '=HYPERLINK("x")', '', '']], delimiter=';')
            mapping = {'02_res.partner.csv': convert_bas.DRAFT_MAPPING['02_res.partner.csv']}
            columns, rows, problems = convert_core.convert_rows(
                convert_core.read_export(os.path.join(source, 'partners.csv')), mapping['02_res.partner.csv']['columns'],
                convert_core.template_header(os.path.join(templates, '02_res.partner.csv')))
            self.assertEqual(columns[-1], 'td_bas_code', "the external code of BAS is kept")
            self.assertEqual(rows[0][0], 'td_md.res_partner_00_001')
            self.assertEqual(rows[0][-1], '00-001')
            self.assertEqual(rows[1][1], '\'=HYPERLINK("x")', "a formula is written as text")
            self.assertFalse(problems)

    def test_ac_089_missing_columns_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            for folder in ('src', 'tpl', 'out'):
                os.mkdir(os.path.join(tmp, folder))
            self._write(os.path.join(tmp, 'tpl', '05_product.product.csv'), [['id', 'name', 'default_code', 'type']])
            self._write(os.path.join(tmp, 'src', 'materials.csv'), [['Name'], ['Board 18']], delimiter=';')
            code = convert_bazis.main(['--source', os.path.join(tmp, 'src'), '--templates', os.path.join(tmp, 'tpl'),
                                       '--out', os.path.join(tmp, 'out')])
            self.assertEqual(code, 1, "the column «Article» is not in the export: warning, non-zero exit")
            with open(os.path.join(tmp, 'out', '05_product.product.csv'), encoding='utf-8') as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(rows[0][:4], ['id', 'name', 'default_code', 'type'])
            self.assertEqual(rows[1][1], 'Board 18')


@tagged('post_install', '-at_install')
class TestMigrationCheck(AccountTestInvoicingCommon):
    """AC-089, AC-090: the reconciliation report — Odoo against the source."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        env.user.group_ids |= env.ref('sales_team.group_sale_manager') | env.ref('td_mebli_base.group_finance') \
            | env.ref('stock.group_stock_manager')
        cls.board = env['product.product'].create({'name': 'Board 18 white', 'is_storable': True,
                                                   'taxes_id': [(5, 0, 0)]})
        cls.service = env['product.product'].create({'name': 'Kitchen', 'type': 'consu', 'is_storable': True,
                                                     'invoice_policy': 'order', 'taxes_id': [(5, 0, 0)]})
        warehouse = env['stock.warehouse'].search([('company_id', '=', env.company.id)], limit=1)
        quant = env['stock.quant'].create({'product_id': cls.board.id, 'location_id': warehouse.lot_stock_id.id,
                                           'inventory_quantity': 40})
        quant.action_apply_inventory()
        cls.orders = env['sale.order']
        for price, paid in ((1000.0, 300.0), (2000.0, 0.0)):
            order = env['sale.order'].create({
                'partner_id': cls.partner_a.id, 'client_order_ref': f'BAS-{int(price)}',
                'order_line': [(0, 0, {'product_id': cls.service.id, 'product_uom_qty': 1, 'price_unit': price})]})
            order.action_confirm()
            if paid:
                invoice = order._create_invoices()
                invoice.action_post()
                env['account.payment.register'].with_context(active_model='account.move', active_ids=invoice.ids)\
                    .create({'amount': paid})._create_payments()
            cls.orders |= order

    def _check(self, prepayment, orders, stock, **extra):
        return self.env['td.mebli.migration.check'].create({'name': 'Start', 'line_ids': [
            (0, 0, {'metric': 'prepayment', 'value_source': prepayment}),
            (0, 0, {'metric': 'open_orders', 'value_source': orders}),
            (0, 0, {'metric': 'stock', 'product_id': self.board.id, 'value_source': stock}),
        ] + extra.get('lines', [])})

    def test_ac_089_report_reconciled_when_equal(self):
        check = self._check(300.0, 2, 40.0, lines=[(0, 0, {'metric': 'prepayment', 'order_ref': 'BAS-1000',
                                                            'value_source': 300.0})])
        check.action_td_compute()
        self.assertEqual([round(v, 2) for v in check.line_ids.mapped('value_odoo')], [300.0, 2.0, 40.0, 300.0])
        self.assertEqual(check.state, 'reconciled')
        self.assertFalse(check.line_ids.cause_order_ids)
        pdf, _type = self.env['ir.actions.report']._render_qweb_html('td_mebli_migration.report_migration_check',
                                                                     check.ids)
        self.assertIn(b'Migration Reconciliation', pdf)

    def test_ac_090_difference_shows_the_causes_and_needs_a_signed_explanation(self):
        check = self._check(500.0, 2, 38.0)
        check.action_td_compute()
        self.assertEqual(check.state, 'diff')
        prepayment = check.line_ids.filtered(lambda l: l.metric == 'prepayment')
        self.assertAlmostEqual(prepayment.diff, -200.0)
        self.assertEqual(prepayment.cause_order_ids, self.orders[0], "the order with a prepayment is the record to check")
        self.assertAlmostEqual(check.line_ids.filtered(lambda l: l.metric == 'stock').diff, 2.0)
        with self.assertRaises(ValidationError):
            check.state = 'reconciled'  # not with a difference
        with self.assertRaises(UserError):
            check.action_td_sign_explanation()  # no explanation
        clerk = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Finance', 'login': 'td_mig_fin',
            'group_ids': [(6, 0, [self.env.ref('td_mebli_base.group_finance').id])]})
        check.explanation = 'Prepayment of 200 is a cash payment booked in BAS after the date'
        with self.assertRaises(AccessError):
            check.with_user(clerk).action_td_sign_explanation()  # a manager signs
        check.action_td_sign_explanation()
        self.assertEqual((check.state, check.explained_by), ('explained', self.env.user))
        with self.assertRaises(UserError):
            check.action_td_compute()  # closed

    def test_ac_089_import_steps_follow_the_templates_of_a13(self):
        steps = self.env['td.mebli.migration.step'].search([])
        self.assertEqual(steps.mapped('sequence'), list(range(1, 20)))
        self.assertEqual(steps[0].template, '01_product.category.csv')
        action = steps[0].action_td_import()
        self.assertEqual((action['tag'], action['params']['model']), ('import', 'product.category'))
        missing = steps.filtered(lambda s: not s.model_installed)
        for step in missing:
            with self.assertRaises(UserError):
                step.action_td_import()
