from datetime import datetime, timedelta

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.td_mebli_sale.tests.common import TdMebliSaleCommon

PHOTO = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='


@tagged('post_install', '-at_install')
class TestInstall(TransactionCase):

    def test_signed_final_act_gives_the_crew_percent(self):
        env = self.env
        partner = env['res.partner'].create({'name': 'Customer'})
        project = env['project.project'].create({'name': 'Installation', 'allow_billable': True})
        # the standard: a service «installation» of the order creates the visit task in the installation project
        product = env['product.product'].create({'name': 'Kitchen installation', 'list_price': 40000.0, 'type': 'service',
                                                 'service_tracking': 'task_global_project', 'project_id': project.id})
        order = env['sale.order'].create({'partner_id': partner.id, 'order_line': [(0, 0, {'product_id': product.id})]})
        order.action_confirm()
        user = env['res.users'].with_context(no_reset_password=True).create(
            {'name': 'Fitter', 'login': 'td_fitter', 'group_ids': [(6, 0, [env.ref('project.group_project_user').id])]})
        employee = env['hr.employee'].create({'name': 'Fitter', 'user_id': user.id, 'hourly_cost': 100.0})
        task = order.tasks_ids
        self.assertEqual(len(task), 1)
        task.user_ids = user
        act = env['td.mebli.install.act'].create({'task_id': task.id, 'kind': 'final', 'crew_pct': 5.0})
        self.assertEqual(act.order_id, order)
        self.assertAlmostEqual(act.crew_amount, 2000.0)
        with self.assertRaises(UserError):
            act.action_sign()
        act.write({'signature': PHOTO, 'signed_by': 'Customer',
                   'defect_ids': [(0, 0, {'name': 'Gap on the left door'})]})
        act.action_sign()
        self.assertEqual(act.state, 'signed')
        self.assertEqual(act.defect_open_count, 1)
        self.assertEqual(task.state, '1_done')
        env['td.mebli.accrual'].action_td_accrue()
        accrual = env['td.mebli.accrual'].search([('act_id', '=', act.id)])
        self.assertEqual(accrual.employee_id, employee)
        self.assertAlmostEqual(accrual.amount, 2000.0)
        env['td.mebli.accrual'].action_td_accrue()  # twice: no double accrual
        self.assertEqual(env['td.mebli.accrual'].search_count([('act_id', '=', act.id)]), 1)
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                env['td.mebli.accrual'].create({'employee_id': employee.id, 'kind': 'penalty', 'amount': -500.0})


@tagged('post_install', '-at_install')
class TestPiecework(TdMebliSaleCommon):
    """Decision AI-08: the piecework is the piece rate of the operation, not the hours times the hourly cost."""

    def test_piece_rate_of_the_operation_shared_by_time(self):
        env = self.env
        first = env['hr.employee'].create({'name': 'First', 'pin': '1111', 'hourly_cost': 999.0})
        second = env['hr.employee'].create({'name': 'Second', 'pin': '2222', 'hourly_cost': 1.0})
        order = self._make_order()
        order.action_confirm()
        workorder = order.mrp_production_ids.workorder_ids[:1]
        operation = workorder.operation_id
        operation.td_piece_rate = 10.0
        basis = operation._td_basis_quantity()
        self.assertGreater(basis, 0)
        kiosk = env['td.mebli.kiosk']
        kiosk.create({'workorder_id': workorder.id, 'action': 'start', 'employee_id': first.id, 'pin': '1111'}).action_confirm()
        kiosk.create({'workorder_id': workorder.id, 'action': 'done', 'employee_id': first.id, 'pin': '1111'}).action_confirm()
        self.assertEqual(workorder.state, 'done')
        start = datetime(2026, 11, 2, 8, 0)
        workorder.time_ids.write({'date_start': start, 'date_end': start + timedelta(minutes=90)})
        productive = env['mrp.workcenter.productivity.loss'].search([('loss_type', '=', 'productive')], limit=1)
        env['mrp.workcenter.productivity'].create({
            'workorder_id': workorder.id, 'workcenter_id': workorder.workcenter_id.id, 'loss_id': productive.id,
            'td_employee_id': second.id, 'date_start': start, 'date_end': start + timedelta(minutes=30)})
        env['td.mebli.accrual'].action_td_accrue()
        accruals = env['td.mebli.accrual'].search([('productivity_id', 'in', workorder.time_ids.ids)])
        total = 10.0 * basis * workorder.qty_produced
        self.assertAlmostEqual(sum(accruals.mapped('amount')), total, places=1)
        first_amount = accruals.filtered(lambda a: a.employee_id == first).amount
        self.assertAlmostEqual(first_amount, round(total * 0.75, 2))  # the share of the time, not the hourly cost
        self.assertEqual(set(accruals.mapped('piece_rate')), {10.0})
        env['td.mebli.accrual'].action_td_accrue()  # twice: no double accrual
        self.assertEqual(env['td.mebli.accrual'].search_count([('productivity_id', 'in', workorder.time_ids.ids)]), 2)


@tagged('post_install', '-at_install')
class TestInstallAccess(TdMebliSaleCommon):
    """Record rules of the acts and the accruals; «Accrue» by the accountant without manufacturing rights."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env

        def user(login, groups):
            return env['res.users'].with_context(no_reset_password=True).create(
                {'name': login, 'login': login, 'group_ids': [(6, 0, [env.ref(g).id for g in groups])]})
        cls.fitter = user('td_fitter_a', ['project.group_project_user'])
        cls.stranger = user('td_fitter_b', ['project.group_project_user'])
        cls.manager = user('td_pm', ['project.group_project_manager'])
        # the finance role of the demo: sales manager, accountant, stock user, dashboard; no manufacturing group
        cls.fin = user('td_fin', ['sales_team.group_sale_manager', 'account.group_account_user', 'stock.group_stock_user'])
        cls.employee = env['hr.employee'].create({'name': 'Fitter A', 'user_id': cls.fitter.id})
        private = env['project.project'].create({'name': 'Installation', 'privacy_visibility': 'followers'})
        partner = env['res.partner'].create({'name': 'Customer'})
        cls.order = env['sale.order'].create({'partner_id': partner.id, 'order_line': [
            (0, 0, {'product_id': env['product.product'].create({'name': 'Montage', 'type': 'service',
                                                                   'list_price': 10000.0}).id})]})
        cls.order.action_confirm()
        cls.task = env['project.task'].create({'name': 'Visit', 'project_id': private.id, 'partner_id': partner.id,
                                               'sale_line_id': cls.order.order_line.id,
                                               'user_ids': [(6, 0, cls.fitter.ids)]})
        cls.task.sale_order_id = cls.order
        assert cls.task.sale_order_id == cls.order
        cls.act = env['td.mebli.install.act'].create({'task_id': cls.task.id, 'kind': 'final', 'crew_pct': 5.0})

    def test_act_visible_as_its_visit(self):
        Act = self.env['td.mebli.install.act']
        self.assertEqual(Act.with_user(self.fitter).search([('id', '=', self.act.id)]), self.act)
        self.assertFalse(Act.with_user(self.stranger).search([('id', '=', self.act.id)]))
        self.assertEqual(Act.with_user(self.manager).search([('id', '=', self.act.id)]), self.act)
        with self.assertRaises(AccessError):
            self.act.with_user(self.stranger).write({'crew_pct': 7.0})

    def test_signed_act_is_read_only_and_amount_fixed(self):
        act = self.act.with_user(self.fitter)
        act.write({'signature': PHOTO, 'signed_by': 'Customer'})
        act.action_sign()
        self.assertEqual(self.act.state, 'signed')
        amount = self.act.crew_amount
        for user in (self.fitter, self.manager):
            with self.assertRaises(AccessError):
                self.act.with_user(user).write({'crew_pct': 10.0})
        self.order.order_line.price_unit = 20000.0  # the order changes later: the signed act keeps its amount
        self.env.flush_all()
        self.assertAlmostEqual(self.act.crew_amount, amount)
        self.act.with_user(self.fitter).message_post(body='Photo of the gap')  # the chatter stays open

    def test_one_final_act_per_order(self):
        with self.assertRaises(ValidationError):
            self.env['td.mebli.install.act'].create({'task_id': self.task.id, 'kind': 'final'})
        self.env['td.mebli.install.act'].create({'task_id': self.task.id, 'kind': 'stage'})

    def test_accountant_accrues_and_confirmed_is_fixed(self):
        self.act.write({'signature': PHOTO})
        self.act.action_sign()
        Accrual = self.env['td.mebli.accrual'].with_user(self.fin)
        Accrual.action_td_accrue()
        accrual = Accrual.search([('act_id', '=', self.act.id)])
        self.assertEqual(accrual.employee_id, self.employee)
        accrual.action_td_confirm()
        with self.assertRaises(UserError):
            accrual.write({'amount': 1.0})
        with self.assertRaises(AccessError):  # the salesperson is not allowed to accrue
            seller = self.env['res.users'].with_context(no_reset_password=True).create({
                'name': 'Seller', 'login': 'td_seller',
                'group_ids': [(6, 0, [self.env.ref('sales_team.group_sale_salesman').id])]})
            self.env['td.mebli.accrual'].with_user(seller).action_td_accrue()

    def test_accrual_of_another_company_is_hidden(self):
        other = self.env['res.company'].create({'name': 'Other factory'})
        accrual = self.env['td.mebli.accrual'].create({'employee_id': self.employee.id, 'kind': 'bonus', 'amount': 10.0,
                                                       'reason': 'Clean site', 'company_id': other.id})
        self.assertFalse(self.env['td.mebli.accrual'].with_user(self.fin).search([('id', '=', accrual.id)]))

    def test_defect_visible_as_its_act(self):
        defect = self.env['td.mebli.install.defect'].create({'act_id': self.act.id, 'name': 'Gap of the door'})
        Defect = self.env['td.mebli.install.defect']
        self.assertEqual(Defect.with_user(self.fitter).search([('id', '=', defect.id)]), defect)
        self.assertEqual(Defect.with_user(self.manager).search([('id', '=', defect.id)]), defect)
        self.assertFalse(Defect.with_user(self.stranger).search([('id', '=', defect.id)]))
        with self.assertRaises(AccessError):
            defect.with_user(self.stranger).read(['name'])

    def test_amount_of_the_signature_is_a_stored_field(self):
        self.act.write({'signature': PHOTO})
        self.act.with_user(self.fitter).action_sign()
        self.assertAlmostEqual(self.act.crew_amount_signed, 500.0)
        self.assertAlmostEqual(self.act.crew_amount, 500.0)
        self.order.order_line.price_unit = 30000.0
        self.act.invalidate_recordset()
        self.assertAlmostEqual(self.act.crew_amount, 500.0)
        # an act created already signed (import) keeps the amount of its creation
        stage = self.env['td.mebli.install.act'].create({'task_id': self.task.id, 'kind': 'stage', 'state': 'signed'})
        self.assertEqual(stage.crew_amount, 0.0)

    def test_hours_of_an_accrual_are_not_typed(self):
        accrual = self.env['td.mebli.accrual'].with_user(self.fin).create({
            'employee_id': self.employee.id, 'kind': 'bonus', 'amount': 10.0, 'reason': 'Clean site'})
        with self.assertRaises(UserError):
            accrual.with_user(self.fin).write({'hours': 8.0})
