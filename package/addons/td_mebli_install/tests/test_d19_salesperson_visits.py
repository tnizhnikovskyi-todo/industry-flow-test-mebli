import json
from datetime import datetime

import polib

from odoo.exceptions import AccessError
from odoo.tests import HttpCase, tagged
from odoo.tools.misc import file_path


@tagged('post_install', '-at_install')
class TestD19SalespersonPlansVisits(HttpCase):
    """D-19 (AC-044, UC-01 step 11): the salon manager (Sales only, no Project rights) opens the «Installation Calendar»
    from Sales and plans the visits of his orders — the date and the crew; not other fields, not other orders."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        env.company.td_install_in_price = False
        sale = env.ref('sales_team.group_sale_salesman').id
        cls.salon = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'D-19 salon', 'login': 'td_d19_salon', 'password': 'td_d19_salon',
            'group_ids': [(6, 0, [env.ref('base.group_user').id, sale])]})
        cls.salon2 = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'D-19 salon 2', 'login': 'td_d19_salon2', 'password': 'td_d19_salon2',
            'group_ids': [(6, 0, [env.ref('base.group_user').id, sale])]})
        cls.crew = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'D-19 crew', 'login': 'td_d19_crew',
            'group_ids': [(6, 0, [env.ref('base.group_user').id, env.ref('project.group_project_user').id])]})
        cls.partner = env['res.partner'].create({'name': 'D-19 customer'})
        project = env['project.project'].create({'name': 'D-19 installations', 'allow_billable': True,
                                                 'privacy_visibility': 'employees'})
        service = env['product.product'].create({
            'name': 'D-19 installation', 'list_price': 1000.0, 'type': 'service', 'taxes_id': [(5, 0, 0)],
            'invoice_policy': 'order', 'service_tracking': 'task_global_project', 'project_id': project.id})
        cls.orders = env['sale.order']
        for user in (cls.salon, cls.salon2):
            order = env['sale.order'].create({'partner_id': cls.partner.id, 'user_id': user.id,
                                              'order_line': [(0, 0, {'product_id': service.id})]})
            order.action_confirm()
            cls.orders |= order
        cls.visit, cls.other_visit = cls.orders[0].tasks_ids, cls.orders[1].tasks_ids
        assert cls.visit and cls.other_visit

    def test_salesperson_has_no_project_rights(self):
        self.assertFalse(self.salon.has_group('project.group_project_user'))

    def test_menu_in_sales(self):
        """The menu «Installation Calendar» in Sales for the salesperson (the one of Project stays for Project users)."""
        menu = self.env.ref('td_mebli_install.td_mebli_install_calendar_sale_menu')
        self.assertIn(menu.id, self.env['ir.ui.menu'].with_user(self.salon)._visible_menu_ids())
        self.assertNotIn(self.env.ref('project.menu_main_pm').id,
                         self.env['ir.ui.menu'].with_user(self.salon)._visible_menu_ids(), "no Project app for him")

    def test_plan_the_visit_of_his_order(self):
        """The date (drag in the calendar) and the crew of the visit of his order are written."""
        task = self.visit.with_user(self.salon)
        task.write({'date_deadline': datetime(2026, 12, 3, 9, 0)})
        task.write({'user_ids': [(6, 0, [self.crew.id])]})
        self.assertEqual(self.visit.date_deadline, datetime(2026, 12, 3, 9, 0))
        self.assertEqual(self.visit.user_ids, self.crew)

    def test_not_other_fields_nor_other_orders(self):
        with self.assertRaises(AccessError):
            self.visit.with_user(self.salon).write({'name': 'Renamed'})
        with self.assertRaises(AccessError):
            self.visit.with_user(self.salon).write({'description': 'Changed'})
        with self.assertRaises(AccessError):
            self.other_visit.with_user(self.salon).write({'date_deadline': datetime(2026, 12, 4, 9, 0)})
        with self.assertRaises(AccessError):
            self.env['project.task'].with_user(self.salon).create({'name': 'New visit', 'project_id': self.visit.project_id.id})
        with self.assertRaises(AccessError):
            self.visit.with_user(self.salon).unlink()

    def test_project_user_unchanged(self):
        """The crew (Project user) still writes any field of a visible visit."""
        self.other_visit.with_user(self.crew).write({'name': 'Visit renamed by the crew'})

    def test_ui_calendar_as_salesperson(self):
        """In the browser session of the salesperson: the menu comes with load_menus, the calendar view of the action is
        served and the drop of the visit on another day is saved (web_save, as the calendar of the web client)."""
        self.authenticate('td_d19_salon', 'td_d19_salon')
        menus = json.loads(self.url_open('/web/webclient/load_menus').text)
        menu = self.env.ref('td_mebli_install.td_mebli_install_calendar_sale_menu')
        self.assertIn(str(menu.id), {str(key) for key in menus})
        action = self.env.ref('td_mebli_install.td_mebli_install_calendar_action')
        self.make_jsonrpc_request('/web/action/load', {'action_id': action.id})
        self.make_jsonrpc_request('/web/dataset/call_kw/project.task/get_views', {
            'model': 'project.task', 'method': 'get_views', 'args': [],
            'kwargs': {'views': [[self.env.ref('project.view_task_calendar').id, 'calendar'], [False, 'form']]}})
        self.make_jsonrpc_request('/web/dataset/call_kw/project.task/web_save', {
            'model': 'project.task', 'method': 'web_save', 'args': [[self.visit.id], {'date_deadline': '2026-12-05 09:00:00'}],
            'kwargs': {'specification': {'date_deadline': {}}}})
        self.visit.invalidate_recordset()
        self.assertEqual(self.visit.date_deadline, datetime(2026, 12, 5, 9, 0))


@tagged('post_install', '-at_install')
class TestCancelWizardInUkrainian(HttpCase):
    """A-16b (D-16, i18n): the name of the model of the cancel wizard in the refusal of access is Ukrainian for a
    Ukrainian session (the refusal reads the name of the model in the language of the request, ir_model.py:2198)."""

    def test_refusal_names_the_wizard_in_ukrainian(self):
        po = polib.pofile(file_path('td_mebli_install/i18n/uk.po'))
        entry = po.find('Cancel Confirmed Accruals')
        self.assertTrue(entry and entry.msgstr)
        if not self.env['res.lang']._lang_get('uk_UA').active:
            self.skipTest("uk_UA is not loaded in this database")
        user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Accountant', 'login': 'td_i18n_fin', 'lang': 'uk_UA',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id, self.env.ref('account.group_account_user').id])]})
        with self.assertRaises(AccessError) as caught:
            self.env['td.mebli.accrual.cancel'].with_user(user).with_context(lang='uk_UA').create({'reason': 'x'})
        self.assertIn(entry.msgstr, str(caught.exception))
        self.assertNotIn('Cancel Confirmed Accruals', str(caught.exception))
