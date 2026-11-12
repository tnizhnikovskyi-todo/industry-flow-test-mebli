from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

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
