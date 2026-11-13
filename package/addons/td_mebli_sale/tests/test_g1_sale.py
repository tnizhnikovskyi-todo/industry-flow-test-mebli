from ast import literal_eval
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import HttpCase, tagged

from .common import TdMebliSaleCommon

MARGIN_FIELDS = {'sale.order': ['margin', 'margin_percent'],
                 'sale.order.line': ['margin', 'margin_percent', 'purchase_price', 'td_planned_material_cost',
                                     'td_planned_operation_cost']}


@tagged('post_install', '-at_install')
class TestG1Sale(TdMebliSaleCommon):
    """A-11 G1: S-01/S-02/S-05/S-18 — AC-014, AC-016, AC-018, AC-033, AC-036, AC-043, AC-064, AC-066, AC-067, AC-083,
    AC-119."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        env['res.lang']._activate_lang('uk_UA')
        env['ir.module.module']._load_module_terms(['td_mebli_sale'], ['uk_UA'], overwrite=True)
        cls.supplier = env['res.partner'].create({'name': 'Фарбувальня Тест'})
        cls.fronts = env['product.product'].create({
            'name': 'Painted fronts', 'type': 'consu', 'is_storable': True, 'standard_price': 900.0,
            'route_ids': [(6, 0, [env.ref('stock.route_warehouse0_mto').id,
                                  env.ref('purchase_stock.route_warehouse0_buy').id])],
            'seller_ids': [(0, 0, {'partner_id': cls.supplier.id, 'price': 900.0, 'delay': 10})],
        })
        cls.template_bom.write({'produce_delay': 5,
                                'bom_line_ids': [(0, 0, {'product_id': cls.fronts.id, 'product_qty': 2.0})]})

    def _user(self, login, *groups, company=None):
        company = company or self.env.company
        return self.env['res.users'].with_context(no_reset_password=True).create({
            'name': login, 'login': login, 'company_id': company.id, 'company_ids': [(6, 0, company.ids)],
            'group_ids': [(6, 0, [self.env.ref(g).id for g in ('base.group_user',) + groups])]})

    def _confirmed(self, promised_in):
        order = self._make_order()
        start = fields.Date.context_today(order, order.date_order)
        order.commitment_date = fields.Datetime.to_datetime(start + timedelta(days=promised_in))
        order.action_confirm()
        return order, start

    # ------------------------------------------------------------------ S-01
    def test_ac_014_three_products_three_boms_three_mos(self):
        order = self._make_order(width=1000)
        line = order.order_line
        line.copy({'order_id': order.id, 'td_width': 1200})
        line.copy({'order_id': order.id, 'td_width': 800})
        self.assertEqual(len(order.order_line), 3)
        order.action_confirm()
        boms = order.order_line.td_bom_id
        self.assertEqual(len(boms), 3, "one order specification per product line")
        self.assertTrue(all(boms.mapped('td_order_bom')))
        productions = order.mrp_production_ids
        self.assertEqual(len(productions), 3, "one manufacturing order per product line")
        self.assertEqual(productions.bom_id, boms)
        self.assertEqual(order.td_production_count, 3, "the smart button «Production»")
        action = order.action_td_view_production()
        self.assertEqual(set(action['domain'][0][2]), set(productions.ids))

    def test_ac_016_ordinary_product_pricelist_price(self):
        product = self.env['product.product'].create({'name': 'Ручка меблева', 'list_price': 120.0})
        order = self.env['sale.order'].create({'partner_id': self.partner.id,
                                               'order_line': [(0, 0, {'product_id': product.id})]})
        line = order.order_line
        self.assertFalse(line.td_is_parametric)
        self.assertEqual(line.td_size_factor, 1.0)
        self.assertEqual(line.price_unit, 120.0)

    # ------------------------------------------------------------------ S-02
    def test_ac_018_margin_hidden_from_salesperson(self):
        env = self.env
        env.company.td_margin_to_salesman = False
        salesman = self._user('td_g1_salesman', 'sales_team.group_sale_salesman')
        manager = self._user('td_g1_sale_manager', 'sales_team.group_sale_manager')
        finance = self._user('td_g1_finance', 'sales_team.group_sale_salesman_all_leads', 'td_mebli_base.group_finance')
        order = self._make_order()
        order.user_id = salesman
        for model, names in MARGIN_FIELDS.items():
            record = order if model == 'sale.order' else order.order_line
            hidden = env[model].with_user(salesman).fields_get(names)
            self.assertFalse(hidden, "%s: no cost or margin fields for the salesperson" % model)
            with self.assertRaises(AccessError):
                record.with_user(salesman).read(names)
            for user in (manager, finance):
                self.assertEqual(set(env[model].with_user(user).fields_get(names)), set(names))
                record.with_user(user).read(names)
        # the form, the list and the reports of the salesperson have no margin
        form = env['sale.order'].with_user(salesman).get_views([(False, 'form'), (False, 'list')])
        for view in form['views'].values():
            self.assertNotIn('name="margin"', view['arch'])
            self.assertNotIn('td_planned_material_cost', view['arch'])
        menus = env['ir.ui.menu'].with_user(salesman)._visible_menu_ids()
        self.assertNotIn(env.ref('td_mebli_sale.sale_order_line_td_cost_menu').id, menus)
        self.assertIn(env.ref('td_mebli_sale.sale_order_line_td_cost_menu').id,
                      env['ir.ui.menu'].with_user(manager)._visible_menu_ids())
        self.assertFalse(env['sale.report'].with_user(salesman).fields_get(['margin']))
        # the parameter on: the salesperson sees the margin (td_mebli_base.group_margin_view)
        env.company.td_margin_to_salesman = True
        salesman.invalidate_recordset()
        self.assertEqual(set(env['sale.order'].with_user(salesman).fields_get(['margin'])), {'margin'})

    def test_ac_033_lawyer_mark_goes_away(self):
        env = self.env
        env.company.td_contract_mode = 'contract'
        env.company.td_legal_checked = False
        order = self._make_order()
        report = env['ir.actions.report']
        html, _kind = report._render_qweb_html('td_mebli_sale.report_contract', order.ids)
        self.assertIn(b'td_lawyer_mark', html)
        self.assertIn(b'td_mebli_report', html, "AC-N.06: the font of the package with Cyrillic")
        order.partner_id.lang = 'uk_UA'  # the contract is printed in the language of the customer
        html, _kind = report._render_qweb_html('td_mebli_sale.report_contract', order.ids)
        self.assertIn('Шаблон до перевірки юристом (№17)'.encode(), html)
        env.company.td_legal_checked = True
        html, _kind = report._render_qweb_html('td_mebli_sale.report_contract', order.ids)
        self.assertNotIn(b'td_lawyer_mark', html)

    def test_ac_043_installation_in_the_price(self):
        if 'service_tracking' not in self.env['product.template']._fields:
            self.skipTest("sale_project is not installed")
        env = self.env
        project = env['project.project'].create({'name': 'Монтажі', 'allow_billable': True})
        service = env['product.product'].create({'name': 'Монтаж', 'type': 'service', 'list_price': 1500,
                                                 'service_tracking': 'task_global_project', 'project_id': project.id})
        env.company.td_install_in_price = True
        order = env['sale.order'].create({'partner_id': self.partner.id, 'order_line': [(0, 0, {'product_id': service.id})]})
        self.assertEqual(order.order_line.price_unit, 0.0, "installation in the price of the order: zero line")
        order.action_confirm()
        task = order.tasks_ids
        self.assertEqual(len(task), 1, "the visit task is created by the standard (service_tracking)")
        self.assertEqual(task.partner_id, self.partner)
        env.company.td_install_in_price = False
        order2 = env['sale.order'].create({'partner_id': self.partner.id, 'order_line': [(0, 0, {'product_id': service.id})]})
        self.assertEqual(order2.order_line.price_unit, 1500)

    def test_ac_036_changes_by_company(self):
        env = self.env
        fop = env['res.company'].create({'name': 'ФОП Тест'})
        order, _start = self._confirmed(30)
        change = env['td.mebli.order.change'].create({'order_id': order.id, 'version': 2, 'reason': 'customer',
                                                      'note': 'Інший декор'})
        self.assertEqual(change.company_id, order.company_id)
        fop_partner = env['res.partner'].create({'name': 'Покупець ФОП', 'company_id': fop.id})
        fop_order = env['sale.order'].with_company(fop).create({'partner_id': fop_partner.id, 'company_id': fop.id})
        fop_change = env['td.mebli.order.change'].create({'order_id': fop_order.id, 'version': 2, 'reason': 'company',
                                                          'note': 'x'})
        user = self._user('td_g1_change_tov', 'sales_team.group_sale_manager')
        Change = env['td.mebli.order.change'].with_user(user)
        self.assertEqual(Change.search([('id', 'in', (change | fop_change).ids)]), change)
        with self.assertRaises(AccessError):
            fop_change.with_user(user).read(['note'])

    def test_ac_064_salesperson_cannot_drag_the_stage(self):
        order, _start = self._confirmed(30)
        salesman = self._user('td_g1_stage', 'sales_team.group_sale_salesman')
        order.user_id = salesman
        with self.assertRaises(UserError) as error:
            order.with_user(salesman).with_context(lang='uk_UA').td_stage = 'progress'
        self.assertEqual(str(error.exception),
                         "Етап рахується з документів; запуск виробництва — лише начальник виробництва")
        self.assertEqual(order.td_stage, 'confirmed')

    # ------------------------------------------------------------------ S-05 board
    def test_ac_066_reason_on_the_card_and_grouping(self):
        env = self.env
        supplier_late, start = self._confirmed(20)
        supplier_late._get_purchase_orders().order_line.date_planned = fields.Datetime.to_datetime(
            start + timedelta(days=40))
        self.assertGreater(supplier_late.td_delay_days, 0)
        self.assertEqual(supplier_late.td_delay_reason, 'supplier')
        company_late, start = self._confirmed(20)
        company_late.mrp_production_ids.date_finished = fields.Datetime.to_datetime(start + timedelta(days=35))
        self.assertEqual(company_late.td_delay_reason, 'company')
        customer_late, start = self._confirmed(20)
        change = env['td.mebli.order.change'].create({'order_id': customer_late.id, 'version': 2,
                                                      'reason': 'customer', 'note': 'Інший декор'})
        change.action_fix()
        customer_late.mrp_production_ids.date_finished = fields.Datetime.to_datetime(start + timedelta(days=35))
        self.assertEqual(customer_late.td_delay_reason, 'customer', "the reason comes from the version of the change")
        with patch.object(type(env['sale.order']), '_td_distributor_date', lambda self: start + timedelta(days=60)):
            company_late._td_recompute_forecast()
            self.assertEqual(company_late.td_delay_reason, 'distributor')
        company_late._td_recompute_forecast()
        self.assertEqual(company_late.td_delay_reason, 'company')
        # the list grouped by the reason (KPI 2) and the red card of the board
        orders = supplier_late | company_late | customer_late
        groups = env['sale.order'].formatted_read_group([('id', 'in', orders.ids)], ['td_delay_reason'],
                                                       ['td_delay_days:sum'])
        self.assertEqual({g['td_delay_reason'] for g in groups}, {'supplier', 'company', 'customer'})
        kanban = env['sale.order'].get_views([(env.ref('td_mebli_sale.view_order_kanban_td_mebli').id, 'kanban')])
        arch = kanban['views']['kanban']['arch']
        self.assertIn('border-danger', arch)
        self.assertIn('td_delay_reason', arch)
        labels = dict(env['sale.order'].with_context(lang='uk_UA')._fields['td_delay_reason']._description_selection(
            env(context=dict(env.context, lang='uk_UA'))))
        self.assertEqual(labels['customer'], 'Клієнт')
        self.assertEqual(labels['distributor'], "Порізка в дистриб'ютора")

    def test_ac_067_stuck_orders_follow_the_parameter(self):
        env = self.env
        order, _start = self._confirmed(30)
        fresh, _start = self._confirmed(30)
        self.assertTrue(order.td_stage_date)
        order.sudo().write({'td_stage_date': fields.Datetime.now() - timedelta(days=6)})
        env.company.td_stuck_days = 5
        Order = env['sale.order']
        self.assertEqual(Order.search([('td_is_stuck', '=', True), ('id', 'in', (order | fresh).ids)]), order)
        self.assertTrue(order.td_is_stuck)
        env.company.td_stuck_days = 10
        order.invalidate_recordset(['td_is_stuck'])
        self.assertFalse(Order.search([('td_is_stuck', '=', True), ('id', 'in', (order | fresh).ids)]),
                         "the parameter 10: not stuck, without a restart")
        self.assertEqual(Order.search([('td_is_stuck', '!=', True), ('id', 'in', (order | fresh).ids)]), order | fresh)
        # a real change of the stage moves the date
        before = order.td_stage_date
        order.mrp_production_ids.workorder_ids[:1].button_start()
        order.invalidate_recordset(['td_stage', 'td_stage_date'])
        self.assertEqual(order.td_stage, 'progress')
        self.assertGreater(order.td_stage_date, before)
        search = env.ref('td_mebli_sale.view_order_board_search_td_mebli')
        self.assertIn('td_is_stuck', search.arch)

    def test_ac_083_delayed_deliveries(self):
        env = self.env
        order, start = self._confirmed(20)
        line = order._get_purchase_orders().order_line
        line.order_id.button_confirm()
        production = order.mrp_production_ids
        line.date_planned = fields.Datetime.to_datetime(production.date_start.date() + timedelta(days=4))
        line.invalidate_recordset()
        self.assertEqual(line.td_need_date, fields.Date.context_today(line, production.date_start))
        self.assertEqual(line.td_late_days, 4)
        self.assertEqual(line.td_sale_order_ids, order)
        storekeeper = self._user('td_g1_storekeeper', 'stock.group_stock_user')
        action = env['ir.actions.act_window']._for_xml_id('td_mebli_sale.purchase_order_line_td_delayed_action')
        domain = literal_eval(action['domain'])
        found = env['purchase.order.line'].with_user(storekeeper).search(domain)
        self.assertIn(line, found)
        self.assertEqual(line.with_user(storekeeper).action_td_open_sale_orders()['res_id'], order.id)
        self.assertIn(env.ref('td_mebli_sale.purchase_order_line_td_delayed_menu_stock').id,
                      env['ir.ui.menu'].with_user(storekeeper)._visible_menu_ids())
        # in time: not in the list
        line.date_planned = fields.Datetime.to_datetime(production.date_start.date() - timedelta(days=12))
        line.invalidate_recordset()
        self.assertNotIn(line, env['purchase.order.line'].search(domain))

    # ------------------------------------------------------------------ S-18 changes
    def test_ac_119_after_cutting_only_an_additional_order(self):
        order, _start = self._confirmed(30)
        Wizard = self.env['td.mebli.order.change.wizard']
        self.assertEqual(order._td_cut_version(), 0)
        self.assertEqual(order.action_td_open_change()['context']['default_kind'], 'change', "nothing sent: a change")
        bom = order.order_line.td_bom_id
        bom._td_mark_sent_to_cutting()
        bom._td_mark_sent_to_cutting()  # sent again: version 2
        self.assertEqual(order._td_cut_version(), 2)
        action = order.action_td_open_change()
        self.assertEqual(action['context']['default_kind'], 'reorder')
        wizard = Wizard.create({'order_id': order.id, 'note': 'Інший фасад', 'kind': 'change'})
        self.assertEqual(wizard.cut_version, 2)
        with self.assertRaises(UserError) as error:
            wizard.with_context(lang='uk_UA').action_create()
        self.assertEqual(str(error.exception),
                         "Специфікацію відправлено в розкрій (версія 2) — зміна лише дозамовленням")
        self.assertFalse(order.td_change_ids)
        Wizard.create({'order_id': order.id, 'note': 'Додаткова полиця', 'kind': 'reorder'}).action_create()
        self.assertEqual(order.td_change_ids.kind, 'reorder')
        # the parts sent stay locked (AC-052, td_mebli_mrp)
        with self.assertRaises(UserError):
            bom.td_part_ids[:1].write({'qty': 5})

    def test_duplicate_of_a_confirmed_order(self):
        """«Duplicate» of a confirmed order: the stage of the board is not copied (its inverse would refuse it), the copy
        is a quotation."""
        order = self._make_order()
        order.action_confirm()
        copy = order.copy()
        self.assertEqual(copy.state, 'draft')
        self.assertEqual(copy.td_stage, 'quote')

    def test_ac_n07_configurator_dimensions_are_box_b(self):
        """AC-011/012 (VP-02 `configurator`): the dimensions of the order line are shown only with the feature group."""
        salesman = self._user('td_g1_conf', 'sales_team.group_sale_salesman_all_leads')
        arch = lambda: self.env['sale.order'].with_user(salesman).get_views([(False, 'form')])['views']['form']['arch']  # noqa: E731
        self.assertNotIn('name="td_width"', arch(), "box A: no dimensions in the order line")
        salesman.group_ids = [(4, self.env.ref('td_mebli_base.group_feature_configurator').id)]
        self.env.registry.clear_cache('templates')
        self.assertIn('name="td_width"', arch())


@tagged('post_install', '-at_install')
class TestG1ChangeSign(HttpCase, TdMebliSaleCommon):
    """AC-120 (box B): the customer signs the fixed change in the portal of the order."""

    def test_ac_120_change_signed_in_the_portal(self):
        env = self.env
        self.partner.email = 'buyer@example.com'
        order = self._make_order()
        order.action_confirm()
        env['td.mebli.order.change.wizard'].create({'order_id': order.id, 'note': 'Інший декор'}).action_create()
        change = order.td_change_ids
        order.action_td_fix_change()
        # the function is of box B: without the feature group the button is refused
        salesman = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Продавець', 'login': 'td_g1_sign', 'group_ids': [(6, 0, [
                env.ref('sales_team.group_sale_salesman_all_leads').id])]})
        with self.assertRaises(AccessError):
            change.with_user(salesman).action_td_send_sign()
        salesman.group_ids = [(4, env.ref('td_mebli_base.group_feature_change_sign').id)]
        action = change.with_user(salesman).action_td_send_sign()
        self.assertEqual(action['context']['default_template_id'], env.ref('td_mebli_sale.mail_template_td_change_sign').id)
        self.assertTrue(change.td_sign_requested)
        # the portal page shows the version with the price and the date
        url = order.get_portal_url()
        page = self.url_open(url)
        self.assertEqual(page.status_code, 200)
        self.assertIn('td_change_sign_%s' % change.id, page.text)
        # a wrong token: refused
        sign_url = '/my/orders/%s/change/%s/sign' % (order.id, change.id)
        bad = self.make_jsonrpc_request(sign_url, {'access_token': 'wrong', 'name': 'Покупець', 'signature': 'aGVsbG8='})
        self.assertIn('error', bad)
        self.assertEqual(change.state, 'done')
        signature = 'R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=='
        result = self.make_jsonrpc_request(sign_url, {'access_token': order.access_token, 'name': 'Покупець',
                                                      'signature': signature})
        self.assertNotIn('error', result)
        change.invalidate_recordset()
        self.assertEqual(change.state, 'signed')
        self.assertTrue(change.signed_on)
        self.assertEqual(change.signed_by, 'Покупець')
        again = self.make_jsonrpc_request(sign_url, {'access_token': order.access_token, 'name': 'X',
                                                     'signature': signature})
        self.assertIn('error', again, "signed once")
