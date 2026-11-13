from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged

# the cards that searched without a company before (review of A-11, MAJOR-1): their drill-downs are checked here
CARDS = ('on_time', 'claims', 'payments', 'load', 'conversion')


@tagged('post_install', '-at_install')
class TestDashboardCompanies(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.main = cls.env.company
        cls.other = cls.env['res.company'].create({'name': 'Second furniture factory'})
        cls.partner = cls.env['res.partner'].create({'name': 'Customer of the factories'})
        cls.service = cls.env['product.product'].create({'name': 'Kitchen set', 'type': 'service', 'list_price': 1000.0})
        cls.g2 = {}
        cls.data = {company.id: cls._factory_data(company) for company in (cls.main, cls.other)}

    @classmethod
    def _factory_data(cls, company):
        """One record of every card in the company: a signed final act of an unpaid order, a claim, a running work
        order of this week and a measurement sheet."""
        env = cls.env(context=dict(cls.env.context, allowed_company_ids=company.ids))
        order = env['sale.order'].create({
            'partner_id': cls.partner.id, 'company_id': company.id,
            'commitment_date': fields.Datetime.now(),
            'order_line': [(0, 0, {'product_id': cls.service.id, 'product_uom_qty': 1.0, 'price_unit': 1000.0,
                                   'tax_ids': [(5, 0, 0)]})]})
        project = env['project.project'].create({'name': 'Installation', 'company_id': company.id})
        task = env['project.task'].create({'name': 'Visit', 'project_id': project.id, 'company_id': company.id})
        task.sale_order_id = order
        act = env['td.mebli.install.act'].create({'task_id': task.id, 'kind': 'final', 'crew_pct': 0.0})
        act.write({'state': 'signed', 'signed_on': fields.Datetime.now()})
        claim = env['repair.order'].create({'partner_id': cls.partner.id, 'td_claim_order_id': order.id,
                                            'company_id': company.id})
        center = env['mrp.workcenter'].create({'name': f'Edge {company.id}', 'company_id': company.id,
                                               'resource_calendar_id': company.resource_calendar_id.id})
        product = env['product.product'].create({'name': f'Door {company.id}', 'is_storable': True,
                                                 'company_id': company.id})
        bom = env['mrp.bom'].create({'product_tmpl_id': product.product_tmpl_id.id, 'company_id': company.id,
                                     'operation_ids': [(0, 0, {'name': 'Edge', 'workcenter_id': center.id,
                                                               'time_cycle_manual': 30})]})
        production = env['mrp.production'].create({'product_id': product.id, 'bom_id': bom.id,
                                                    'company_id': company.id})
        production.action_confirm()
        production.workorder_ids.button_start()
        sheet = env['td.mebli.measure'].create({'room': 'Kitchen', 'company_id': company.id})
        # the documents of the G2 rules (AC-036): cutting job, packing list, quality journal, mapping template
        cls.g2[company.id] = {
            'td.mebli.cutting.job': env['td.mebli.cutting.job'].create({'production_ids': [(6, 0, production.ids)],
                                                                       'company_id': company.id}),
            'td.mebli.kit.line': env['td.mebli.kit.line'].create({'order_id': order.id, 'item': 'Side panel'}),
            'td.mebli.quality.check': env['td.mebli.quality.check'].create({
                'workorder_id': production.workorder_ids.id, 'name': 'Edge glue', 'result': 'fail'}),
            'td.mebli.import.template': env['td.mebli.import.template'].create({
                'name': 'Bazis', 'company_id': company.id, 'header_signature': f'sig-{company.id}',
                'mapping_json': {'name': 0}}),
        }
        return {'on_time': order, 'payments': order, 'claims': claim, 'load': production.workorder_ids,
                'conversion': sheet}

    def _director(self, company):
        group_ids = [self.env.ref(xmlid).id for xmlid in ('base.group_user', 'td_mebli_dashboard.group_td_mebli_director')]
        return self.env['res.users'].with_context(no_reset_password=True).create({
            'name': f'Director {company.id}', 'login': f'td_dash_dir_{company.id}', 'company_id': company.id,
            'company_ids': [(6, 0, (self.main | self.other).ids)], 'group_ids': [(6, 0, group_ids)]})

    def test_ac_036_director_sees_only_the_selected_company(self):
        """The dashboard works with sudo: every card of a director of company 1 counts only company 1, and the
        same director, switched to company 2, sees only company 2 (the drill-down = the records counted)."""
        for company, foreign in ((self.main, self.other), (self.other, self.main)):
            director = self._director(company)
            data = self.env['td.mebli.dashboard'].with_user(director).with_context(
                allowed_company_ids=company.ids).get_data()
            for key in CARDS:
                drill = set(data['by_key'][key]['drill']['ids'])
                own, alien = self.data[company.id][key], self.data[foreign.id][key]
                self.assertTrue(set(own.ids) <= drill, (company.name, key))
                self.assertFalse(set(alien.ids) & drill, (company.name, key, 'data of the other company'))
            self.assertIn('1', data['by_key']['payments']['lines'][0])  # «Orders: 1» — only the own order is due

    def test_ac_036_two_selected_companies_see_both(self):
        """A director who selected both companies in the switcher sees the sum of both."""
        director = self._director(self.main)
        data = self.env['td.mebli.dashboard'].with_user(director).with_context(
            allowed_company_ids=(self.main | self.other).ids).get_data()
        for key in CARDS:
            drill = set(data['by_key'][key]['drill']['ids'])
            for company in (self.main, self.other):
                self.assertTrue(set(self.data[company.id][key].ids) <= drill, (key, company.name))

    def test_ac_036_g2_documents_by_company(self):
        """The company rules of G2 (cutting job, packing list, quality journal, mapping template), checked on two
        companies: a technologist of company 1 sees only the documents of company 1, also by id."""
        groups = ['base.group_user', 'mrp.group_mrp_user', 'stock.group_stock_user',
                  'sales_team.group_sale_salesman_all_leads']
        tech = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Technologist of company 1', 'login': 'td_dash_tech_mc', 'company_id': self.main.id,
            'company_ids': [(6, 0, self.main.ids)], 'group_ids': [(6, 0, [self.env.ref(g).id for g in groups])]})
        for model in self.g2[self.main.id]:
            own, alien = self.g2[self.main.id][model], self.g2[self.other.id][model]
            self.assertEqual(own.company_id, self.main, model)
            self.assertEqual(alien.company_id, self.other, model)
            found = self.env[model].with_user(tech).search([('id', 'in', (own | alien).ids)])
            self.assertEqual(found, own, model)
            with self.assertRaises(AccessError, msg=model):
                alien.with_user(tech).read(['company_id'])
