from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'td_mebli_ee')
class TestEeBridge(TransactionCase):
    """AC-128: runs only on Odoo Enterprise (the bridge is not installed on Community, AC-130)."""

    def test_ac_128_bridge_installed_with_its_enterprise_app(self):
        Module = self.env['ir.module.module']
        self.assertEqual(Module.search([('name', '=', 'td_mebli_planning')]).state, 'installed')
        self.assertEqual(Module.search([('name', '=', 'planning')]).state, 'installed')

    def test_ac_128_enterprise_fields_and_hidden_screens(self):
        """The fields of the Enterprise models the bridge relies on (assumptions until ВП-4) and the hidden screens."""
        fields = self.env['planning.slot']._fields
        for field in ['resource_id', 'start_datetime', 'end_datetime', 'name', 'company_id']:
            self.assertIn(field, fields, 'assumption of tr/ee-bridges.md: planning.slot.%s exists on Enterprise' % field)
        menu = self.env.ref('td_mebli_install.td_mebli_install_calendar_menu')
        self.assertIn(self.env.ref('td_mebli_planning.group_td_old_screens'), menu.group_ids, 'the td_ screen is hidden by a group')
        # A-14 pr-review m7: with the other bridge installed too, its group is kept (no bridge overwrites the other)
        other = self.env.ref('td_mebli_fsm.group_td_old_screens', raise_if_not_found=False)
        if other:
            self.assertIn(other, menu.group_ids)
        self.assertLessEqual(len(menu.group_ids), 2)

    def test_ac_128_crew_gets_planning_shifts(self):
        employee = self.env['hr.employee'].create({'name': 'Fitter EE', 'user_id': self.env.user.id}) \
            if not self.env.user.employee_id else self.env.user.employee_id
        project = self.env['project.project'].create({'name': 'Installations EE'})
        task = self.env['project.task'].create({'name': 'Visit', 'project_id': project.id,
                                                'user_ids': [(6, 0, self.env.user.ids)],
                                                'date_deadline': '2026-11-20 08:00:00'})
        task.action_td_plan_crew()
        self.assertEqual(task.td_slot_ids.resource_id, employee.resource_id)
