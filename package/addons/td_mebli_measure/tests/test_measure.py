from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMeasure(TransactionCase):

    def test_fridge_deeper_than_the_niche(self):
        sheet = self.env['td.mebli.measure'].create({'room': 'Kitchen'})
        niche = self.env['td.mebli.measure.niche'].create(
            {'measure_id': sheet.id, 'name': 'Column', 'width_mm': 600, 'height_mm': 2100, 'depth_mm': 560})
        fridge = self.env['td.mebli.measure.appliance'].create(
            {'measure_id': sheet.id, 'niche_id': niche.id, 'name': 'Fridge', 'width_mm': 595, 'height_mm': 2010,
             'depth_mm': 590})
        oven = self.env['td.mebli.measure.appliance'].create(
            {'measure_id': sheet.id, 'niche_id': niche.id, 'name': 'Oven', 'width_mm': 595, 'height_mm': 595,
             'depth_mm': 550})
        self.assertNotEqual(sheet.name, '/')
        self.assertFalse(fridge.fits)
        self.assertIn('30', fridge.issue)
        self.assertTrue(oven.fits)
        self.assertEqual(sheet.issue_count, 1)
        sheet.action_check()
        self.assertEqual(sheet.state, 'checked')

    def test_own_measurements_and_lead_from_the_order(self):
        env = self.env

        def user(login, groups):
            return env['res.users'].with_context(no_reset_password=True).create(
                {'name': login, 'login': login, 'group_ids': [(6, 0, [env.ref(g).id for g in groups])]})
        measurer = user('td_measurer', ['sales_team.group_sale_salesman'])
        other = user('td_other_salesman', ['sales_team.group_sale_salesman'])
        manager = user('td_sale_manager', ['sales_team.group_sale_manager'])
        sheet = env['td.mebli.measure'].create({'room': 'Kitchen', 'measurer_id': measurer.id})
        Measure = env['td.mebli.measure']
        self.assertEqual(Measure.with_user(measurer).search([('id', '=', sheet.id)]), sheet)
        self.assertFalse(Measure.with_user(other).search([('id', '=', sheet.id)]))
        self.assertEqual(Measure.with_user(manager).search([('id', '=', sheet.id)]), sheet)
        self.assertEqual(sheet.company_id, env.company)
        # the opportunity comes from the order (standard sale_crm)
        partner = env['res.partner'].create({'name': 'Customer'})
        lead = env['crm.lead'].create({'name': 'Kitchen', 'partner_id': partner.id, 'type': 'opportunity'})
        order = env['sale.order'].create({'partner_id': partner.id, 'opportunity_id': lead.id, 'user_id': other.id})
        sheet.order_id = order
        self.assertEqual(sheet.lead_id, lead)
        self.assertEqual(Measure.with_user(other).search([('id', '=', sheet.id)]), sheet)  # the salesperson of the order
