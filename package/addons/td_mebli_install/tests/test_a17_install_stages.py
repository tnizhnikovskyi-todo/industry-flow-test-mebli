from datetime import datetime

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestA17InstallStages(TransactionCase):
    """A-17 №16 (AC-140): the project of the installations has the stages of the visits; the visit gets the date from
    the delivery date of the order and moves «To Plan» → «Planned» with it; a new delivery date moves the visit."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        env.company.td_install_in_price = False
        cls.project = env['project.project'].create({'name': 'A-17 installations', 'allow_billable': True,
                                                     'td_install_project': True})
        cls.service = env['product.product'].create({
            'name': 'A-17 installation', 'list_price': 0.0, 'type': 'service', 'invoice_policy': 'order',
            'service_tracking': 'task_global_project', 'project_id': cls.project.id})
        cls.partner = env['res.partner'].create({'name': 'A-17 customer'})
        cls.stage = {key: env.ref(f'td_mebli_install.stage_install_{key}')
                     for key in ('to_plan', 'planned', 'installed', 'act_signed', 'cancelled')}

    def _order(self, when=None):
        order = self.env['sale.order'].create({'partner_id': self.partner.id, 'commitment_date': when,
                                               'order_line': [(0, 0, {'product_id': self.service.id})]})
        order.action_confirm()
        return order

    def test_stages_of_the_install_project(self):
        self.assertEqual(self.project.type_ids.sorted('sequence'), self.stage['to_plan'] | self.stage['planned']
                         | self.stage['installed'] | self.stage['act_signed'] | self.stage['cancelled'])
        other = self.env['project.project'].create({'name': 'Other'})
        self.assertFalse(other.type_ids & self.stage['to_plan'], "only the project of the installations")
        other.td_install_project = True
        self.assertIn(self.stage['to_plan'], other.type_ids, "the flag set later links the stages")

    def test_visit_date_from_the_delivery_date(self):
        when = datetime(2026, 12, 3, 9, 0)
        task = self._order(when).tasks_ids
        self.assertEqual(task.date_deadline, when)
        self.assertEqual(task.stage_id, self.stage['planned'])

    def test_visit_without_date_to_plan_then_planned(self):
        order = self._order()
        task = order.tasks_ids
        self.assertFalse(task.date_deadline)
        self.assertEqual(task.stage_id, self.stage['to_plan'])
        order.commitment_date = datetime(2026, 12, 5, 10, 0)
        self.assertEqual(task.date_deadline, datetime(2026, 12, 5, 10, 0), "the visit without a date gets it")
        self.assertEqual(task.stage_id, self.stage['planned'])

    def test_new_delivery_date_moves_only_the_unchanged_visit(self):
        order = self._order(datetime(2026, 12, 3, 9, 0))
        task = order.tasks_ids
        order.commitment_date = datetime(2026, 12, 4, 9, 0)
        self.assertEqual(task.date_deadline, datetime(2026, 12, 4, 9, 0))
        task.date_deadline = datetime(2026, 12, 10, 8, 0)  # planned by hand
        order.commitment_date = datetime(2026, 12, 6, 9, 0)
        self.assertEqual(task.date_deadline, datetime(2026, 12, 10, 8, 0), "a visit planned by hand keeps its date")

    def test_signed_final_act_moves_the_visit(self):
        task = self._order(datetime(2026, 12, 3, 9, 0)).tasks_ids
        act = self.env['td.mebli.install.act'].create({'task_id': task.id, 'kind': 'final'})
        act.write({'state': 'signed'})
        self.assertEqual(task.stage_id, self.stage['act_signed'])
