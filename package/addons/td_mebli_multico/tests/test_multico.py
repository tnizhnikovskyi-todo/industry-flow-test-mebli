from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMultico(TransactionCase):
    """AC-035 (F-25, AI-14): the installation by another legal entity (FOP) is its own service order."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        env['res.lang']._activate_lang('uk_UA')
        cls.tov = env.company
        cls.fop = env['res.company'].create({'name': 'ФОП Монтажник'})
        cls.partner = env['res.partner'].create({'name': 'Покупець', 'email': 'buyer@example.com'})
        cls.project_tov = env['project.project'].create({'name': 'Монтажі ТОВ', 'allow_billable': True,
                                                         'company_id': cls.tov.id})
        cls.project_fop = env['project.project'].with_company(cls.fop).create({
            'name': 'Монтажі ФОП', 'allow_billable': True, 'company_id': cls.fop.id})
        cls.service = env['product.product'].create({'name': 'Монтаж', 'type': 'service', 'list_price': 2000,
                                                     'service_tracking': 'task_global_project',
                                                     'project_id': cls.project_tov.id})
        cls.service.product_tmpl_id.with_company(cls.fop).project_id = cls.project_fop
        cls.cabinet = env['product.product'].create({'name': 'Шафа', 'list_price': 30000})
        cls.both = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Менеджер обох', 'login': 'td_multico_both', 'company_id': cls.tov.id,
            'company_ids': [(6, 0, (cls.tov | cls.fop).ids)],
            'group_ids': [(6, 0, [env.ref('sales_team.group_sale_salesman_all_leads').id,
                                  env.ref('base.group_multi_company').id,
                                  env.ref('project.group_project_user').id])]})

    def _order(self, user):
        return self.env['sale.order'].with_user(user).with_context(
            allowed_company_ids=(self.tov | self.fop).ids).create({
                'partner_id': self.partner.id, 'td_install_company_id': self.fop.id,
                'order_line': [(0, 0, {'product_id': self.cabinet.id}), (0, 0, {'product_id': self.service.id})]})

    def test_ac_035_install_order_of_the_fop(self):
        self.tov.td_install_in_price = False
        order = self._order(self.both)
        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        install = order.td_install_order_ids
        self.assertEqual(len(install), 1, "a separate service order of the installation")
        self.assertEqual(install.company_id, self.fop)
        self.assertEqual(install.partner_id, self.partner)
        self.assertEqual(install.td_parent_order_id, order)
        self.assertEqual(install.state, 'sale')
        self.assertEqual(install.order_line.product_id, self.service)
        self.assertEqual(install.order_line.price_unit, 2000)
        # the lines of the main order are not split: the installation line is moved, not duplicated
        self.assertEqual(order.order_line.product_id, self.cabinet)
        self.assertFalse(order.sudo().tasks_ids, "the seller has no installation task")
        task = install.sudo().tasks_ids
        self.assertEqual(len(task), 1)
        self.assertEqual(task.company_id, self.fop, "the visit task belongs to the FOP")
        self.assertEqual(task.project_id, self.project_fop)
        # smart buttons in both orders
        self.assertEqual(order.td_install_order_count, 1)
        self.assertEqual(order.action_td_view_install_orders()['res_id'], install.id)
        self.assertEqual(install.td_parent_order_name, order.name)
        self.assertEqual(install.action_td_view_parent_order()['res_id'], order.id)

    def test_ac_035_installation_in_the_price(self):
        self.tov.td_install_in_price = True
        order = self._order(self.both)
        order.action_confirm()
        self.assertEqual(order.td_install_order_ids.order_line.price_unit, 0.0)

    def test_ac_035_no_access_to_the_fop(self):
        only_tov = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Менеджер ТОВ', 'login': 'td_multico_tov', 'company_id': self.tov.id,
            'company_ids': [(6, 0, self.tov.ids)],
            'group_ids': [(6, 0, [self.env.ref('sales_team.group_sale_salesman_all_leads').id])]})
        order = self.env['sale.order'].create({'partner_id': self.partner.id, 'td_install_company_id': self.fop.id,
                                               'order_line': [(0, 0, {'product_id': self.service.id})]})
        order.user_id = only_tov
        with self.assertRaises(UserError) as error:
            order.with_user(only_tov).with_context(lang='uk_UA').action_confirm()
        self.assertEqual(str(error.exception), "У вас немає доступу до компанії ФОП Монтажник — монтаж від неї оформлює "
                                               "користувач цієї компанії")
        self.assertEqual(order.state, 'draft')

    def test_ac_035_cancel_main_order_activity_for_the_fop(self):
        order = self._order(self.both)
        order.action_confirm()
        install = order.td_install_order_ids
        order.with_context(disable_cancel_warning=True)._action_cancel()
        self.assertEqual(install.state, 'sale', "the FOP document is not cancelled automatically")
        self.assertTrue(install.activity_ids)

    def test_ac_036_fop_order_hidden_from_the_tov_user(self):
        order = self._order(self.both)
        order.action_confirm()
        only_tov = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Менеджер ТОВ 2', 'login': 'td_multico_tov2', 'company_id': self.tov.id,
            'company_ids': [(6, 0, self.tov.ids)],
            'group_ids': [(6, 0, [self.env.ref('sales_team.group_sale_salesman_all_leads').id])]})
        self.assertFalse(self.env['sale.order'].with_user(only_tov).search([('id', '=', order.td_install_order_ids.id)]))
        self.assertEqual(order.with_user(only_tov).td_install_order_count, 1, "the count is read with sudo")
