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

    def test_scenario(self):
        result = run(self.env)
        order = result['order']
        line = order.order_line
        self.assertGreater(line.price_unit, 28000)
        self.assertTrue(line.td_bom_id)
        self.assertEqual(order.state, 'sale')
        productions = result['productions']
        self.assertEqual(len(productions), 2)
        self.assertEqual(set(productions.mapped('state')), {'done'})
        job = result['job']
        self.assertEqual(job.state, 'done')
        self.assertTrue(self.env['stock.lot'].search_count([('td_cutting_job_id', '=', job.id)]))
        self.assertGreater(line.margin, 0)
