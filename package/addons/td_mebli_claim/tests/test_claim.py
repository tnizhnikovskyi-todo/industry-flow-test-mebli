from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.td_mebli_sale.tests.common import TdMebliSaleCommon

PHOTO = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='


class ClaimCommon(TdMebliSaleCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['res.lang']._activate_lang('uk_UA')
        cls.category = cls.env['product.category'].create({'name': 'Kitchens'})
        cls.cabinet_tmpl.categ_id = cls.category

    def _confirmed(self):
        order = self._make_order()
        order.action_confirm()
        return order

    def _claim(self, order, **vals):
        return self.env['repair.order'].create(dict({'partner_id': self.partner.id, 'td_claim_order_id': order.id}, **vals))


@tagged('post_install', '-at_install')
class TestClaim(ClaimCommon):

    def test_claim_on_the_order_and_remake(self):
        order = self._confirmed()
        claim = self._claim(order, product_id=self.cabinet.id, under_warranty=True,
                            tag_ids=[(0, 0, {'name': 'Production defect'})])
        self.assertEqual(claim.tag_ids.name, 'Production defect')  # the reason is the standard tag
        self.assertEqual(order.td_claim_count, 1)
        claim.action_td_remake()
        self.assertEqual(claim.td_remake_production_id.product_id, self.cabinet)
        self.assertEqual(claim.td_remake_production_id.origin, claim.name)

    def test_bought_product_is_not_remade(self):
        bought = self.env['product.product'].create({'name': 'Painted front', 'type': 'consu'})
        claim = self._claim(self._confirmed(), product_id=bought.id)
        with self.assertRaises(UserError):  # a bought product without a part is ordered again, not remade
            claim.action_td_remake()

    def test_ac_080_remake_of_the_part(self):
        order = self._confirmed()
        part = order.order_line.td_bom_id.td_part_ids[:1]
        self.assertTrue(part)
        bought = self.env['product.product'].create({'name': 'Painted front', 'type': 'consu'})
        claim = self._claim(order, product_id=bought.id, td_part_id=part.id)
        claim.action_td_remake()
        production = claim.td_remake_production_id
        self.assertEqual(production.origin, claim.name)  # the origin is the number of the claim
        self.assertEqual(production.product_id, self.env.ref('td_mebli_claim.product_remake_part').product_variant_id)
        self.assertEqual(production.state, 'confirmed')  # in the plan of the shop
        self.assertEqual(production.bom_id.td_part_ids.name, part.name)
        self.assertEqual(production.bom_id.td_part_ids.qty, part.qty)
        self.assertIn(part.material_id, production.move_raw_ids.product_id)  # the board of the part
        self.assertEqual(len(production.workorder_ids), len(part.bom_id.operation_ids))
        self.assertIn(production.name, claim.message_ids[:1].body)

    def test_ac_081_no_part_no_product(self):
        claim = self._claim(self._confirmed())
        count = self.env['mrp.production'].search_count([])
        with self.assertRaises(UserError) as error:
            claim.action_td_remake()
        self.assertEqual(str(error.exception), "Choose a part or a product to remake")
        with self.assertRaises(UserError) as error:
            claim.with_context(lang='uk_UA').action_td_remake()
        self.assertEqual(str(error.exception), "Оберіть деталь або виріб для повторного виготовлення")
        self.assertEqual(self.env['mrp.production'].search_count([]), count)
        self.assertFalse(claim.td_remake_production_id)

    def test_ac_110_overdue_by_the_parameter_of_the_company(self):
        order = self._confirmed()
        claim = self._claim(order, product_id=self.cabinet.id)
        self.env.flush_all()
        self.env.cr.execute("UPDATE repair_order SET create_date = %s WHERE id = %s",
                            (fields.Datetime.now() - timedelta(days=10, hours=1), claim.id))
        claim.invalidate_recordset()
        self.env.company.td_claim_overdue_days = 14
        self.assertEqual(claim.td_days_open, 10)
        self.assertFalse(claim.td_overdue)
        self.assertNotIn(claim, self.env['repair.order'].search([('td_overdue', '=', True)]))
        self.env.company.td_claim_overdue_days = 7
        claim.invalidate_recordset()
        self.assertTrue(claim.td_overdue)
        self.assertIn(claim, self.env['repair.order'].search([('td_overdue', '=', True)]))
        claim.schedule_date = fields.Datetime.now() + timedelta(days=30)  # the schedule does not matter, the days do
        claim.invalidate_recordset()
        self.assertTrue(claim.td_overdue)
        action = order.action_td_view_claims()  # the smart button «Claims» of the order
        self.assertEqual(self.env['repair.order'].search(action['domain']), claim)


@tagged('post_install', '-at_install')
class TestWarranty(ClaimCommon):
    """AC-111 / F-55: the warranty is the term of the product category from the date of the final act."""

    def _installed(self, days_ago):
        order = self._confirmed()
        project = self.env['project.project'].create({'name': 'Installation'})
        task = self.env['project.task'].create({'name': 'Visit', 'project_id': project.id})
        task.sale_order_id = order
        act = self.env['td.mebli.install.act'].create({'task_id': task.id, 'kind': 'final', 'signature': PHOTO})
        act.action_sign()
        self.env.flush_all()
        self.env.cr.execute('UPDATE td_mebli_install_act SET signed_on = %s WHERE id = %s',
                            (fields.Datetime.now() - timedelta(days=days_ago), act.id))
        act.invalidate_recordset()
        return order, act

    def test_ac_111_warranty_of_the_category(self):
        self.category.td_warranty_months = 24
        order, act = self._installed(days_ago=100)
        claim = self._claim(order, product_id=self.cabinet.id)
        self.assertEqual(claim.td_warranty_end, act.signed_on.date() + relativedelta(months=24))
        self.assertFalse(claim.td_after_warranty)
        self.assertTrue(claim.under_warranty)
        self.assertEqual(claim.td_warranty_note, "On warranty")

    def test_ac_111_term_not_set(self):
        self.assertFalse(self.category.td_warranty_months)
        self.env['ir.config_parameter'].sudo().set_param('td_mebli_claim.warranty_months', '24')  # not read any more
        order, _act = self._installed(days_ago=100)
        claim = self._claim(order, product_id=self.cabinet.id)
        self.assertTrue(claim.td_warranty_unset)
        self.assertFalse(claim.td_warranty_end)
        self.assertFalse(claim.under_warranty, "the service decides by hand")
        self.assertEqual(claim.td_warranty_note, "Warranty term is not set")
        claim.invalidate_recordset(['td_warranty_note'])
        self.assertEqual(claim.with_context(lang='uk_UA').td_warranty_note, "Гарантійний строк не задано")
        claim.under_warranty = True  # the decision of the service stays
        self.assertTrue(claim.under_warranty)

    def test_after_warranty_the_customer_pays(self):
        self.category.td_warranty_months = 24
        order, _act = self._installed(days_ago=800)
        claim = self._claim(order, product_id=self.cabinet.id)
        self.assertTrue(claim.td_after_warranty)
        self.assertLess(claim.td_warranty_end, fields.Date.today(), "24 months after the final act")
        self.assertFalse(claim.under_warranty, "the standard flag: parts are not at price 0")
        recent, _act = self._installed(days_ago=10)
        self.assertTrue(self._claim(recent, product_id=self.cabinet.id).under_warranty)


@tagged('post_install', '-at_install')
class TestClaimVisit(ClaimCommon):

    def test_ac_132_plan_a_visit(self):
        env = self.env
        project = env['project.project'].create({'name': 'Installations', 'allow_billable': True})
        service = env['product.product'].create({'name': 'Installation', 'type': 'service', 'list_price': 0.0,
                                                 'service_tracking': 'task_global_project', 'project_id': project.id})
        self.partner.write({'street': 'Shevchenka 1', 'city': 'Kyiv'})
        order = self._make_order()
        order.order_line = [(0, 0, {'product_id': service.id})]
        order.action_confirm()
        crew = env['res.users'].with_context(no_reset_password=True).create(
            {'name': 'Crew', 'login': 'td_g3_crew', 'group_ids': [(6, 0, [env.ref('project.group_project_user').id])]})
        claim = self._claim(order, product_id=self.cabinet.id)
        claim.action_td_plan_visit()
        task = claim.td_visit_task_id
        self.assertEqual(task.project_id, project)
        self.assertEqual(task.td_claim_id, claim)
        self.assertEqual(task.sale_order_id, order)
        self.assertEqual(task.td_visit_kind, 'service')
        self.assertEqual(task.date_deadline, claim.schedule_date)
        self.assertIn('Shevchenka 1', task.td_address)
        self.assertIn(claim.name, task.name)
        calendar = env.ref('td_mebli_install.td_mebli_install_calendar_action')
        self.assertIn(task, env['project.task'].search(eval(calendar.domain)))  # the calendar of the crews
        task.user_ids = crew
        row = task._td_day_plan_groups()[0][2][0]  # the day plan: the address, nothing to collect
        self.assertIn('Shevchenka 1', row['address'])
        self.assertEqual(row['pay_missing'], 0.0)
        task.action_td_start_install()  # a service visit: no act, no payment control
        self.assertFalse(task.td_act_ids)
        self.assertEqual(task.state, '01_in_progress')

    def test_ac_132_order_without_installation(self):
        claim = self._claim(self._confirmed(), product_id=self.cabinet.id)
        with self.assertRaises(UserError):
            claim.action_td_plan_visit()
