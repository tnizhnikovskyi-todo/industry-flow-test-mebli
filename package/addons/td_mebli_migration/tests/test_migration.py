import csv
import os
import re
import tempfile

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.td_mebli_migration.scripts import convert_bas, convert_bazis, convert_core


@tagged('post_install', '-at_install')
class TestMigrationConverters(AccountTestInvoicingCommon):
    """AC-089: the converters are skeletons (formats ВП-1, ВП-3 unknown); the core maps an export into A-13 templates."""

    def _write(self, path, rows, delimiter=','):
        with open(path, 'w', encoding='utf-8', newline='') as handle:
            csv.writer(handle, delimiter=delimiter).writerows(rows)

    # headers of the A-13 templates (package/master-data v1.1), not their rows
    HEADERS = {
        '02_res.partner.csv': ['id', 'name', 'is_company', 'supplier_rank', 'customer_rank', 'vat', 'company_registry',
                               'phone', 'email'],
        '05_product.product.csv': ['id', 'name', 'default_code', 'type', 'is_storable', 'categ_id/id', 'uom_id/id',
                                   'sale_ok', 'purchase_ok', 'route_ids/id'],
        '13_hr.employee.csv': ['id', 'name', 'job_title', 'pin'],
        'td/19b_res.partner.csv': ['id', 'td_bas_code'],
        'td/20b_product.product.csv': ['id', 'td_bas_code'],
        'td/21b_hr.employee.csv': ['id', 'td_bas_code'],
    }

    def _read(self, path):
        with open(path, encoding='utf-8') as handle:
            return list(csv.reader(handle))

    def test_ac_089_bas_converter_keeps_the_bas_code(self):
        """Return A-13-2: the code of BAS goes into td/19b-21b; the standard templates keep their header (light)."""
        with tempfile.TemporaryDirectory() as tmp:
            source, templates, out = (os.path.join(tmp, name) for name in ('src', 'tpl', 'out'))
            for folder in (source, os.path.join(templates, 'td'), out):
                os.makedirs(folder)
            for name, header in self.HEADERS.items():
                self._write(os.path.join(templates, name), [header])
            self._write(os.path.join(source, 'partners.csv'),
                        [['Код', 'Наименование', 'ИНН', 'ЕДРПОУ'], ['00-001', 'Демо-Постачальник', '', '1'],
                         ['00-002', '=HYPERLINK("x")', '', '']], delimiter=';')
            self._write(os.path.join(source, 'products.csv'),
                        [['Код', 'Наименование', 'Артикул'], ['N-01', 'Board 18', 'B18']], delimiter=';')
            self._write(os.path.join(source, 'employees.csv'),
                        [['Табельный номер', 'Сотрудник', 'Должность'], ['T-7', 'Cutter', 'Operator']], delimiter=';')
            code = convert_bas.main(['--source', source, '--templates', templates, '--out', out])
            self.assertEqual(code, 0)
            self.assertEqual(set(convert_bas.DRAFT_MAPPING), set(self.HEADERS))
            for name, header in self.HEADERS.items():
                rows = self._read(os.path.join(out, name))
                self.assertEqual(rows[0], header, f"{name}: the converter writes the header of the template as it is")
            partners = self._read(os.path.join(out, '02_res.partner.csv'))
            self.assertEqual(partners[1][0], 'td_md.res_partner_00_001')
            self.assertEqual(partners[2][1], '\'=HYPERLINK("x")', "a formula is written as text")
            self.assertEqual(self._read(os.path.join(out, 'td', '19b_res.partner.csv'))[1:],
                             [['td_md.res_partner_00_001', '00-001'], ['td_md.res_partner_00_002', '00-002']],
                             "the external code of BAS is kept, on the same ids as the partners")
            self.assertEqual(self._read(os.path.join(out, 'td', '20b_product.product.csv'))[1],
                             ['td_md.product_product_n_01', 'N-01'])
            self.assertEqual(self._read(os.path.join(out, 'td', '21b_hr.employee.csv'))[1],
                             ['td_md.hr_employee_t_7', 'T-7'])

    def test_ac_089_converter_adds_no_column_to_a_template(self):
        """A column of the mapping that the template has not is not written (it is reported)."""
        columns, rows, problems = convert_core.convert_rows(
            [{'Код': '00-001', 'Наименование': 'Demo'}],
            {'id': {'xmlid': 'res_partner', 'from': 'Код'}, 'name': 'Наименование', 'td_bas_code': 'Код'},
            self.HEADERS['02_res.partner.csv'])
        self.assertEqual(columns, self.HEADERS['02_res.partner.csv'])
        self.assertEqual(len(rows[0]), len(columns))
        self.assertEqual(len(problems), 1)
        self.assertIn('td_bas_code', problems[0])
        for target, spec in convert_bas.DRAFT_MAPPING.items():
            if not target.startswith('td/'):
                self.assertFalse([c for c in spec['columns'] if c.startswith('td_')],
                                 f"{target}: no field td_* in a standard template")

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
        # A-14 security 6 / pr-review m3: the finance does not reset the signed explanation, not even by RPC, and does
        # not change the lines of a closed reconciliation
        with self.assertRaises(AccessError):
            check.with_user(clerk).action_td_reset()
        with self.assertRaises(AccessError):
            check.with_user(clerk).write({'explained_by': clerk.id})
        with self.assertRaises(UserError):
            prepayment.with_user(clerk).write({'value_source': 300.0})
        with self.assertRaises(UserError):
            prepayment.with_user(clerk).unlink()
        self.assertEqual((check.state, check.explained_by, prepayment.value_source),
                         ('explained', self.env.user, 500.0))
        manager = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Sales Manager', 'login': 'td_mig_manager',
            'group_ids': [(6, 0, [self.env.ref('sales_team.group_sale_manager').id])]})
        check.with_user(manager).action_td_reset()
        self.assertEqual((check.state, check.explained_by.id), ('draft', False))
        prepayment.with_user(clerk).write({'value_source': 300.0})  # open again

    def test_ac_090_finance_does_not_bypass_the_signature_by_rpc(self):
        """CHECKS.md No. 29 (security S-N1): the finance computes and writes the explanation of an open reconciliation,
        but by RPC does not set the status, does not change a signed explanation and does not create an «explained»
        reconciliation with somebody's signature."""
        clerk = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Finance 2', 'login': 'td_mig_fin2',
            'group_ids': [(6, 0, [self.env.ref('td_mebli_base.group_finance').id])]})
        check = self._check(500.0, 2, 38.0).with_user(clerk)
        check.action_td_compute()  # the finance computes: the status follows the difference
        self.assertEqual(check.state, 'diff')
        check.explanation = 'Cash payment booked after the date'
        with self.assertRaises(AccessError):
            check.write({'state': 'explained'})
        with self.assertRaises(AccessError):
            check.write({'state': 'draft'})
        check.with_user(self.env.user).action_td_sign_explanation()
        with self.assertRaises(AccessError):
            check.write({'explanation': 'Another reason'})
        with self.assertRaises(AccessError):
            check.write({'state': 'draft'})  # not «Reset» around the manager: the old signature would stay valid
        self.assertEqual((check.state, check.explanation), ('explained', 'Cash payment booked after the date'))
        Check = self.env['td.mebli.migration.check'].with_user(clerk)
        with self.assertRaises(AccessError):
            Check.create({'name': 'Forged', 'state': 'explained', 'explanation': 'x', 'explained_by': self.env.user.id})
        with self.assertRaises(AccessError):
            Check.create({'name': 'Forged 2', 'state': 'reconciled'})
        self.assertTrue(Check.create({'name': 'Draft'}))
        manager = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Sales Manager 2', 'login': 'td_mig_manager2',
            'group_ids': [(6, 0, [self.env.ref('sales_team.group_sale_manager').id])]})
        check.with_user(manager).write({'explanation': 'Corrected by the manager'})
        self.assertEqual(check.explanation, 'Corrected by the manager')

    def test_ac_089_import_steps_follow_the_templates_of_a13(self):
        steps = self.env['td.mebli.migration.step'].search([])
        self.assertEqual(steps.mapped('sequence'), list(range(1, 29)))
        self.assertEqual(steps[0].template, '01_product.category.csv')
        action = steps[0].action_td_import()
        self.assertEqual((action['tag'], action['params']['model']), ('import', 'product.category'))
        missing = steps.filtered(lambda s: not s.model_installed)
        for step in missing:
            with self.assertRaises(UserError):
                step.action_td_import()

    def test_ac_089_import_order_is_the_order_of_the_readme(self):
        """Return A-13-2: steps 1-15 = standard files 01-15, then the files td/ by their number (README v1.1 «Порядок
        імпорту»: td/NN after its standard file, td/19b-21b last). Checked against the README when the package is there."""
        templates = self.env['td.mebli.migration.step'].search([]).mapped('template')
        standard, td = templates[:15], templates[15:]
        self.assertEqual(standard, sorted(standard))
        self.assertTrue(all(not name.startswith('td/') for name in standard))
        self.assertEqual(td, sorted(td))
        self.assertTrue(all(name.startswith('td/') for name in td))
        self.assertEqual(td[-3:], ['td/19b_res.partner.csv', 'td/20b_product.product.csv', 'td/21b_hr.employee.csv'])
        readme = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'master-data', 'README.md')
        if not os.path.exists(readme):
            self.skipTest('package/master-data is not next to the addons')
        with open(readme, encoding='utf-8') as handle:
            files = re.findall(r'^\| (?:td )?\d\d[a-z]? \| `([^`]+\.csv)` \|', handle.read(), re.M)
        self.assertEqual(len(files), 28)
        self.assertEqual(set(templates), set(files), "every template of the README has its step and back")
        folder = os.path.dirname(readme)
        for name in templates:
            self.assertTrue(os.path.exists(os.path.join(folder, name)), name)
        for target, spec in convert_bas.DRAFT_MAPPING.items():
            header = convert_core.template_header(os.path.join(folder, target))
            self.assertLessEqual(set(spec['columns']), set(header), f"{target}: the mapping fits the template")

    def test_ac_089_bas_steps_need_td_mebli_bas(self):
        """td/19b-21b are imported only with td_mebli_bas (VP-04); in the light profile the steps are not available."""
        bas = self.env['ir.module.module'].search([('name', '=', 'td_mebli_bas')]).state == 'installed'
        steps = self.env['td.mebli.migration.step'].search([('template', 'like', 'td/%b_%')])
        bas_steps = steps.filtered(lambda s: s.module_name == 'td_mebli_bas')
        self.assertEqual(bas_steps.mapped('sequence'), [26, 27, 28])
        self.assertEqual(set(bas_steps.mapped('model_installed')), {bas})
        if not bas:
            with self.assertRaises(UserError):
                bas_steps[0].action_td_import()
        self.assertTrue(self.env.ref('td_mebli_migration.step_td_01b').model_installed)
        # Return A-14 (CHECKS №7, A-13-3): the component roles of the configurator go after td/01b and before td/05b
        roles = self.env.ref('td_mebli_migration.step_td_03b') | self.env.ref('td_mebli_migration.step_td_04b')
        self.assertEqual(roles.mapped('sequence'), [17, 18])
        self.assertEqual(set(roles.mapped('module_name')), {'td_mebli_mrp'})
        self.assertEqual(set(roles.mapped('model_installed')), {True})
        self.assertEqual(self.env.ref('td_mebli_migration.step_16').sequence, 19)
        self.assertEqual(self.env.ref('td_mebli_migration.step_01').template, '01_product.category.csv')


@tagged('post_install', '-at_install')
class TestMigrationCompanies(TransactionCase):

    def test_ac_036_reconciliation_lines_by_company(self):
        """Review A-11: the lines of a reconciliation follow its company (a global rule of the lines)."""
        env = self.env
        other = env['res.company'].create({'name': 'Second company of the migration'})
        checks = {company: env['td.mebli.migration.check'].create({
            'name': f'Start {company.name}', 'company_id': company.id,
            'line_ids': [(0, 0, {'metric': 'open_orders', 'value_source': 1})]}) for company in (env.company, other)}
        manager = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Migration manager', 'login': 'td_mig_mc_manager', 'company_id': env.company.id,
            'company_ids': [(6, 0, env.company.ids)],
            'group_ids': [(6, 0, [env.ref('sales_team.group_sale_manager').id])]})
        all_lines = checks[env.company].line_ids | checks[other].line_ids
        Line = env['td.mebli.migration.check.line'].with_user(manager)
        self.assertEqual(Line.search([('id', 'in', all_lines.ids)]), checks[env.company].line_ids)
        with self.assertRaises(AccessError):
            checks[other].line_ids.with_user(manager).read(['metric'])
