from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDayPlan(TransactionCase):
    """F-58: the day plan of the crew — the standard visit tasks of the orders, printed and on the phone."""

    def test_day_plan(self):
        env = self.env
        env.user.tz = 'Europe/Kyiv'
        project = env['project.project'].create({'name': 'Installation', 'allow_billable': True})
        service = env['product.product'].create({'name': 'Installation', 'type': 'service', 'list_price': 100,
                                                 'service_tracking': 'task_global_project', 'project_id': project.id})
        partner = env['res.partner'].create({'name': 'Buyer', 'street': 'Sadova 1', 'city': 'Kyiv', 'phone': '+380000000000'})
        order = env['sale.order'].create({'partner_id': partner.id, 'order_line': [(0, 0, {'product_id': service.id})]})
        order.action_confirm()
        task = order.tasks_ids[:1]
        now = fields.Datetime.now()
        task.write({'date_deadline': now + timedelta(minutes=5), 'user_ids': [(6, 0, env.user.ids)]})
        groups = task._td_day_plan_groups()
        self.assertEqual(len(groups), 1)
        row = groups[0][2][0]
        self.assertEqual(row['order'], order.name)
        self.assertIn('Sadova', row['address'])
        html, _kind = env['ir.actions.report']._render_qweb_html('td_mebli_install.report_day_plan', task.ids)
        self.assertIn(b'td_report_day_plan', html)
        html, _kind = env['ir.actions.report']._render_qweb_html('td_mebli_install.report_day_plan_user', env.user.ids)
        self.assertIn(order.name.encode(), html, "the plan of the crew member: his visits of the coming days")
        action = env['project.task'].action_td_my_day()
        today = env['project.task'].search(action['domain'])
        self.assertIn(task, today, "the visit of today is in «My Day» of the crew member")
