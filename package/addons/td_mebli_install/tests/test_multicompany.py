from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestInstallCompanies(TransactionCase):

    def test_ac_036_defects_and_crew_hours_by_company(self):
        """Review A-11: the defects and the crew hours of an act follow the company of the act (global rules) —
        a project manager of company 1, who reads «all» defects, does not see the lines of company 2."""
        env = self.env
        other = env['res.company'].create({'name': 'Second installation company'})
        lines = {}
        for company in (env.company, other):
            project = env['project.project'].create({'name': 'Installation', 'company_id': company.id})
            task = env['project.task'].create({'name': 'Visit', 'project_id': project.id, 'company_id': company.id})
            act = env['td.mebli.install.act'].create({'task_id': task.id, 'kind': 'final', 'crew_pct': 0.0})
            lines[company] = (env['td.mebli.install.defect'].create({'act_id': act.id, 'name': 'Scratch'}),
                              env['td.mebli.install.act.crew'].create({'act_id': act.id, 'user_id': env.uid, 'hours': 2}))
            self.assertEqual(lines[company][0].company_id, company)
        manager = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Installation manager', 'login': 'td_inst_mc_manager', 'company_id': env.company.id,
            'company_ids': [(6, 0, env.company.ids)],
            'group_ids': [(6, 0, [env.ref('project.group_project_manager').id,
                                  env.ref('sales_team.group_sale_salesman_all_leads').id])]})
        for index, model in enumerate(('td.mebli.install.defect', 'td.mebli.install.act.crew')):
            both = lines[env.company][index] | lines[other][index]
            self.assertEqual(env[model].with_user(manager).search([('id', 'in', both.ids)]), lines[env.company][index])
            with self.assertRaises(AccessError):
                lines[other][index].with_user(manager).read(['act_id'])
        manager.company_ids = [(4, other.id)]
        Defect = env['td.mebli.install.defect'].with_user(manager).with_context(allowed_company_ids=other.ids)
        self.assertEqual(Defect.search([('id', 'in', (lines[env.company][0] | lines[other][0]).ids)]), lines[other][0])
