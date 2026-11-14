from odoo.tests import TransactionCase, tagged

from odoo.addons.td_mebli_demo.scenario import run


@tagged('post_install', '-at_install')
class TestDemoScenario(TransactionCase):

    def test_catalog(self):
        for key, parts in (('prod_wardrobe', 7), ('prod_dresser', 6), ('prod_kitchen', 5)):
            tmpl = self.env.ref(f'td_mebli_demo.{key}')
            self.assertTrue(tmpl.td_is_parametric)
            self.assertEqual(len(tmpl.td_part_rule_ids), parts)
            bom = self.env['mrp.bom']._bom_find(tmpl.product_variant_id)[tmpl.product_variant_id]
            self.assertEqual(len(bom.operation_ids), 4)

    def test_d10_exclusions_of_the_configurator(self):
        """D-10 (AC-011): «decor X — only edge X»: the anthracite body of the wardrobe and the kitchen is not offered
        with the 0.4 mm edge (standard exclusion, the configurator checks the combination), the 2 mm edge is."""
        from odoo.addons.td_mebli_demo.hooks import _ptav
        for key in ('prod_wardrobe', 'prod_kitchen'):
            tmpl = self.env.ref(f'td_mebli_demo.{key}')
            base = sum((_ptav(tmpl, x) for x in ('val_facade_anthr', 'val_fit_std', 'val_w_custom', 'val_h_custom',
                                                 'val_d_custom')), self.env['product.template.attribute.value'])
            anthr = _ptav(tmpl, 'val_body_anthr')
            self.assertFalse(tmpl._is_combination_possible(base | anthr | _ptav(tmpl, 'val_edge_04')), key)
            self.assertTrue(tmpl._is_combination_possible(base | anthr | _ptav(tmpl, 'val_edge_2')), key)
            self.assertTrue(tmpl._is_combination_possible(base | _ptav(tmpl, 'val_body_sonoma') | _ptav(tmpl, 'val_edge_04')), key)
        dresser = self.env.ref('td_mebli_demo.prod_dresser')
        self.assertFalse(dresser.attribute_line_ids.product_template_value_ids.exclude_for, "the dresser has no exclusions")

    def test_scenario(self):
        result = run(self.env)
        order = result['order']
        line = order.order_line
        self.assertGreater(line.price_unit, 24000)
        self.assertTrue(line.td_bom_id)
        self.assertEqual(order.state, 'sale')
        productions = result['productions']
        self.assertEqual(len(productions), 2)
        self.assertEqual(set(productions.mapped('state')), {'done'})
        job = result['job']
        self.assertEqual(job.state, 'done')
        # the offcuts of the job become lots only with the feature «offcut» of box B (G2, AC-059): the demo switches
        # the box B functions it shows on (data/settings_data.xml)
        self.assertTrue(self.env.ref('base.group_user').implied_ids & self.env.ref('td_mebli_base.group_feature_offcut'))
        self.assertTrue(self.env['stock.lot'].search_count([('td_cutting_job_id', '=', job.id)]))
        self.assertGreater(line.margin, 0)


@tagged('post_install', '-at_install')
class TestDemoRoles(TransactionCase):
    """D-08 (package/demo/plan.md §2, tr/security.md §1): the groups of the demo roles."""

    def test_d08_measurer_and_crew_without_sales(self):
        from odoo.addons.td_mebli_demo.showcase import USERS
        groups = {login: set(xmlids) for login, _name, _job, _avatar, xmlids in USERS}
        sales = {'sales_team.group_sale_salesman', 'sales_team.group_sale_salesman_all_leads', 'sales_team.group_sale_manager'}
        self.assertEqual(groups['measure'], {'td_mebli_measure.group_td_mebli_measurer'})
        for login in ('measure', 'fitter', 'fitter2'):
            self.assertFalse(groups[login] & sales, login)
            for xmlid in groups[login]:
                group = self.env.ref(xmlid)
                self.assertFalse(group.all_implied_ids & self.env['res.groups'].browse(
                    [self.env.ref(x).id for x in sales]), f"{login}: {xmlid} implies Sales")
        self.assertIn('td_mebli_claim.group_service', groups['fitter'], "the crew leader is the service (ROLE-10)")
