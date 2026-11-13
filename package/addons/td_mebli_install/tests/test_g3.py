"""A-11 G3: AC-020, AC-021, AC-100, AC-102…AC-108, AC-134 (texts of the errors — SPEC §4.3, §4.10, §4.11, §4.18)."""
from datetime import date, datetime, timedelta

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger

from odoo.addons.td_mebli_sale.tests.common import TdMebliSaleCommon

PHOTO = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='


def _user(env, login, groups):
    return env['res.users'].with_context(no_reset_password=True).create({
        'name': login, 'login': login, 'group_ids': [(6, 0, [env.ref(g).id for g in groups])]})


class G3InstallCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        env['res.lang']._activate_lang('uk_UA')
        # the terms of uk.po: a base without uk_UA (en_US admin) gets them only now (AC-102 prints in the customer language)
        env['ir.module.module']._load_module_terms(['td_mebli_install'], ['uk_UA'], overwrite=True)
        # VP-16 is set explicitly: the tests count the installation line with its price (the package default is
        # `true`, A-14 config 4 — the result must not depend on the answers of the config package)
        cls.env.company.td_install_in_price = False
        cls.company = env.company
        cls.term = env['account.payment.term'].create({'name': '50/40/10', 'line_ids': [
            (0, 0, {'value': 'percent', 'value_amount': 50.0, 'nb_days': 0, 'td_milestone': 'order'}),
            (0, 0, {'value': 'percent', 'value_amount': 40.0, 'nb_days': 14, 'td_milestone': 'install'}),
            (0, 0, {'value': 'percent', 'value_amount': 10.0, 'nb_days': 30, 'td_milestone': 'act'})]})
        cls.partner = env['res.partner'].create({'name': 'Customer'})
        cls.project = env['project.project'].create({'name': 'Installation', 'allow_billable': True})
        cls.service = env['product.product'].create({
            'name': 'Kitchen installation', 'list_price': 10000.0, 'type': 'service', 'taxes_id': [(5, 0, 0)],
            'invoice_policy': 'order', 'service_tracking': 'task_global_project', 'project_id': cls.project.id})
        cls.fin = _user(env, 'td_g3_fin', ['base.group_user', 'td_mebli_base.group_finance'])
        cls.seller = _user(env, 'td_g3_seller', ['sales_team.group_sale_salesman'])
        cls.fitter = _user(env, 'td_g3_fitter', ['project.group_project_user'])
        cls.fitter2 = _user(env, 'td_g3_fitter2', ['project.group_project_user'])
        cls.employee = env['hr.employee'].create({'name': 'Fitter One', 'user_id': cls.fitter.id})
        cls.employee2 = env['hr.employee'].create({'name': 'Fitter Two', 'user_id': cls.fitter2.id})

    def _order(self, terms=True):
        vals = {'partner_id': self.partner.id, 'order_line': [(0, 0, {'product_id': self.service.id})]}
        if terms:
            vals['payment_term_id'] = self.term.id
        order = self.env['sale.order'].create(vals)
        order.action_confirm()
        order.tasks_ids.user_ids = self.fitter | self.fitter2
        return order


@tagged('post_install', '-at_install')
class TestPaymentG3(G3InstallCommon):

    def test_ac_020_warn_posts_in_the_chatter(self):
        """Warn (default VP-06): the action goes on, the chatter of the order says what is missing."""
        self.assertEqual(self.company.td_payment_control, 'warn')
        order = self._order()
        task = order.tasks_ids
        task.action_td_start_install()
        self.assertEqual(task.state, '01_in_progress')
        bodies = ' '.join(order.message_ids.mapped('body'))
        self.assertIn('Payment before installation not received: 9 000.00', bodies)

    def test_ac_020_block_error_of_spec(self):
        """Block: the error of SPEC, the state of the visit does not change; the field of the company, not a parameter."""
        self.company.td_payment_control = 'block'
        order = self._order()
        task = order.tasks_ids
        task.state = '03_approved'
        with self.assertRaises(UserError) as error:
            task.action_td_start_install()
        missing = f"9 000.00 {order.currency_id.symbol}"
        self.assertEqual(str(error.exception),
                         f"Installation blocked: the payment of {missing} is not received. Contact the manager")
        with self.assertRaises(UserError) as error:
            task.with_context(lang='uk_UA').action_td_start_install()
        self.assertEqual(str(error.exception),
                         f"Монтаж заблоковано: не отримано доплату {missing}. Зверніться до менеджера")
        self.assertEqual(task.state, '03_approved')  # the state does not change
        self.assertFalse(task.td_act_ids)
        # the old system parameter of the slice is not read any more
        self.env['ir.config_parameter'].sudo().set_param('td_mebli_install.payment_control', 'warn')
        with self.assertRaises(UserError):
            task.action_td_start_install()

    def test_ac_021_manual_mark_counts_as_paid(self):
        self.company.td_payment_control = 'block'
        order = self._order()
        Mark = self.env['td.mebli.pay.mark'].with_user(self.fin)
        mark = Mark.create({'order_id': order.id, 'amount': 9000.0, 'reason': 'Bank statement of today'})
        order.invalidate_recordset()
        self.assertTrue(order.td_pay_ok)
        self.assertAlmostEqual(order.td_pay_received, 9000.0)
        self.assertEqual(mark.user_id, self.fin)
        body = order.message_ids[:1].body
        self.assertIn('Payment confirmed by hand', body)
        self.assertIn('Bank statement of today', body)
        self.assertIn(self.fin.name, body)
        order.tasks_ids.action_td_start_install()  # the block lets the crew go
        self.assertEqual(len(order.tasks_ids.td_act_ids), 1)
        mark.cancelled = True  # the payment came by the exchange (AC-042): the mark no longer counts
        order.invalidate_recordset()
        self.assertFalse(order.td_pay_ok)
        # review A-11: the amount is fixed after the creation; any change of the mark goes to the chatter
        self.assertIn('Manual payment mark cancelled', order.message_ids[:1].body)
        with self.assertRaisesRegex(UserError, 'is not changed'):
            mark.with_user(self.fin).amount = 1.0
        mark.with_user(self.fin).reason = 'Bank statement of yesterday'
        body = order.message_ids[:1].body
        self.assertIn('Manual payment mark changed', body)
        self.assertIn('Bank statement of today', body)
        self.assertIn('Bank statement of yesterday', body)

    def test_ac_042_cancel_marks_on_bas_payment(self):
        order = self._order()
        self.env['td.mebli.pay.mark'].create({'order_id': order.id, 'amount': 9000.0, 'reason': 'Bank statement'})
        order.invalidate_recordset()
        self.assertTrue(order.td_pay_ok)
        cancelled = order._td_cancel_pay_marks()  # called by the BAS hook of td_mebli_bas (AC-042)
        self.assertEqual(len(cancelled), 1)
        self.assertTrue(all(mark.cancelled for mark in order.td_pay_mark_ids))
        order.invalidate_recordset()
        self.assertFalse(order.td_pay_ok)
        self.assertFalse(order._td_cancel_pay_marks())  # idempotent: nothing left to cancel

    def test_ac_021_reason_required_error_of_spec(self):
        order = self._order()
        Mark = self.env['td.mebli.pay.mark'].with_user(self.fin)
        with self.assertRaises(ValidationError) as error:
            Mark.create({'order_id': order.id, 'amount': 100.0})
        self.assertEqual(str(error.exception), "Specify the reason of the manual payment mark")
        with self.assertRaises(ValidationError) as error:
            Mark.with_context(lang='uk_UA').create({'order_id': order.id, 'amount': 100.0, 'reason': ' '})
        self.assertEqual(str(error.exception), "Вкажіть причину ручної позначки оплати")
        self.assertFalse(order.td_pay_mark_ids)

    def test_ac_021_manager_and_crew_have_no_action(self):
        order = self._order()
        for user in (self.seller, self.fitter):
            with self.assertRaises(AccessError):
                self.env['td.mebli.pay.mark'].with_user(user).create(
                    {'order_id': order.id, 'amount': 100.0, 'reason': 'Paid'})
            with self.assertRaises(AccessError):
                order.with_user(user).action_td_pay_mark()
        action = order.with_user(self.fin).action_td_pay_mark()
        self.assertEqual(action['res_model'], 'td.mebli.pay.mark')
        # the salesperson and the crew read the marks
        mark = self.env['td.mebli.pay.mark'].create({'order_id': order.id, 'amount': 1.0, 'reason': 'Cash'})
        for user in (self.seller, self.fitter):
            self.assertEqual(self.env['td.mebli.pay.mark'].with_user(user).search([('order_id', '=', order.id)]), mark)


@tagged('post_install', '-at_install')
class TestActG3(G3InstallCommon):

    def _signed(self, order, kind='final', **vals):
        act = self.env['td.mebli.install.act'].create(dict({'task_id': order.tasks_ids.id, 'kind': kind}, **vals))
        act.write({'signature': PHOTO, 'signed_by': 'Customer'})
        act.action_sign()
        return act

    def test_ac_098_sign_without_signature_and_change_of_a_signed_act(self):
        """AC-098: SPEC texts «Немає підпису клієнта» / «Підписаний акт змінювати не можна»; the data do not change."""
        order = self._order()
        act = self.env['td.mebli.install.act'].create({'task_id': order.tasks_ids.id, 'kind': 'final'})
        for lang, text in (('en_US', "There is no signature of the customer"), ('uk_UA', "Немає підпису клієнта")):
            with self.assertRaises(UserError) as error:
                act.with_user(self.fitter).with_context(lang=lang).action_sign()
            self.assertEqual(str(error.exception), text)
        self.assertEqual(act.state, 'draft')
        act.write({'signature': PHOTO, 'signed_by': 'Customer'})
        act.with_user(self.fitter).action_sign()
        for lang, text in (('en_US', "A signed act cannot be changed"),
                           ('uk_UA', "Підписаний акт змінювати не можна")):
            with self.assertRaises(UserError) as error:  # the crew of the visit
                act.with_user(self.fitter).with_context(lang=lang).write({'signed_by': 'Somebody else'})
            self.assertEqual(str(error.exception), text)
            with self.assertRaises(UserError) as error:  # «Sign» again
                act.with_user(self.fitter).with_context(lang=lang).action_sign()
            self.assertEqual(str(error.exception), text)
        self.assertEqual(act.signed_by, 'Customer')

    def test_ac_100_photo_archive_needs_the_consent(self):
        order = self._order()
        act = self._signed(order)
        with self.assertRaises(UserError) as error:
            act.with_user(self.fitter).action_td_photo_archive()
        self.assertEqual(str(error.exception), "No consent of the customer to publish the photos")
        with self.assertRaises(UserError) as error:
            act.with_user(self.fitter).with_context(lang='uk_UA').action_td_photo_archive()
        self.assertEqual(str(error.exception), "Немає згоди покупця на публікацію фото")
        self.assertFalse(act.photo_archive)
        with self.assertRaises(ValidationError):
            act.write({'photo_archive': True})
        second = self._signed(self._order(), photo_consent=True)
        second.with_user(self.fitter).action_td_photo_archive()  # the signed act is read only, the button works
        self.assertTrue(second.photo_archive)
        domain = self.env.ref('td_mebli_install.td_mebli_install_act_view_search').arch
        self.assertIn('name="archive" string="Photo Archive"', domain)
        archived = self.env['td.mebli.install.act'].search([('photo_archive', '=', True)])
        self.assertIn(second, archived)
        self.assertNotIn(act, archived)

    def test_ac_102_lawyer_mark_until_checked(self):
        order = self._order()
        act = self._signed(order, defect_ids=[(0, 0, {'name': 'Gap on the left door'})], checklist='Fronts adjusted')
        report = self.env['ir.actions.report']
        # the act is printed in the language of the customer: set explicitly (A-14 convergence 4, not the base language)
        order.partner_id.lang = 'uk_UA'
        html, _kind = report._render_qweb_html('td_mebli_install.report_install_act', act.ids)
        self.assertIn('Шаблон до перевірки юристом'.encode(), html)
        order.partner_id.lang = 'en_US'
        html, _kind = report._render_qweb_html('td_mebli_install.report_install_act', act.ids)
        self.assertIn(b'Template to be checked by a lawyer', html)
        self.assertIn(b'Gap on the left door', html)
        self.assertIn(b'Fronts adjusted', html)
        self.assertIn(b'td_mebli_report', html)  # AC-N.06: the font of the package with the Cyrillic
        self.company.td_legal_checked = True
        html, _kind = report._render_qweb_html('td_mebli_install.report_install_act', act.ids)
        self.assertNotIn(b'Template to be checked by a lawyer', html)

    def test_ac_103_two_visits_by_the_final_act(self):
        """VP-15 «By the final act» (default): the stage act pays nothing, «Closed» only after the final act."""
        self.company.td_crew_pct = 5.0
        order = self._order(terms=False)
        stage = self._signed(order, kind='stage')
        self.assertEqual(stage.crew_amount, 0.0)
        self.env['td.mebli.pay.mark'].create({'order_id': order.id, 'amount': order.amount_total, 'reason': 'Paid'})
        order.invalidate_recordset()
        self.assertEqual(order._td_stage_after_made(), 'install')  # paid, a stage act: not closed yet
        final = self._signed(order, kind='final')
        self.assertAlmostEqual(final.crew_amount, 500.0)  # 10 000 × 5 % of the company
        order.invalidate_recordset()
        self.assertEqual(order._td_stage_after_made(), 'closed')

    def test_ac_103_two_visits_by_stages(self):
        """VP-15 «By stages»: every act pays its share of the work, the final act the rest."""
        self.company.write({'td_crew_base': 'stage', 'td_crew_pct': 5.0})
        order = self._order(terms=False)
        stage = self._signed(order, kind='stage', stage_pct=40.0)
        self.assertAlmostEqual(stage.crew_amount, 200.0)
        final = self._signed(order, kind='final')
        self.assertAlmostEqual(final.crew_amount, 300.0)
        accruals, _no_rate = self.env['td.mebli.accrual']._td_accrue()
        self.assertAlmostEqual(sum(accruals.filtered(lambda a: a.kind == 'crew').mapped('amount')), 500.0)


@tagged('post_install', '-at_install')
class TestAccrualG3(G3InstallCommon):

    def _final(self, hours=None):
        order = self._order(terms=False)
        act = self.env['td.mebli.install.act'].create({'task_id': order.tasks_ids.id, 'kind': 'final', 'crew_pct': 5.0})
        if hours:
            for line in act.crew_line_ids:
                line.hours = hours[line.user_id]
        act.write({'signature': PHOTO})
        act.action_sign()
        return act

    def test_ac_104_crew_percent_equally(self):
        act = self._final()
        self.assertEqual(act.crew_line_ids.user_id, self.fitter | self.fitter2)
        accruals, _no_rate = self.env['td.mebli.accrual']._td_accrue()
        crew = accruals.filtered(lambda a: a.act_id == act)
        self.assertEqual(sorted(crew.mapped('amount')), [250.0, 250.0])

    def test_ac_104_crew_percent_by_time(self):
        self.company.td_crew_split = 'time'
        act = self._final({self.fitter: 3.0, self.fitter2: 1.0})
        accruals, _no_rate = self.env['td.mebli.accrual']._td_accrue()
        crew = accruals.filtered(lambda a: a.act_id == act)
        self.assertAlmostEqual(crew.filtered(lambda a: a.employee_id == self.employee).amount, 375.0)
        self.assertAlmostEqual(crew.filtered(lambda a: a.employee_id == self.employee2).amount, 125.0)
        again, _no_rate = self.env['td.mebli.accrual']._td_accrue()  # the same period again: no double lines
        self.assertFalse(again.filtered(lambda a: a.act_id == act))

    def test_ac_104_crew_of_the_company_once_and_unique(self):
        """Review A-11: the crew percent goes to the employees of the company of the act only (a user can have an
        employee in another company); a cancelled accrual is accrued again; the database refuses a second live one."""
        other = self.env['res.company'].create({'name': 'Second company of the crew'})
        foreign = self.env['hr.employee'].create({'name': 'Fitter One (other)', 'user_id': self.fitter.id,
                                                  'company_id': other.id})
        act = self._final()
        accruals, _no_rate = self.env['td.mebli.accrual']._td_accrue()
        crew = accruals.filtered(lambda a: a.act_id == act)
        self.assertEqual(crew.employee_id, self.employee | self.employee2)
        self.assertNotIn(foreign, crew.employee_id)
        crew.write({'state': 'cancel'})
        again, _no_rate = self.env['td.mebli.accrual']._td_accrue()  # the cancelled ones do not count as accrued
        self.assertEqual(again.filtered(lambda a: a.act_id == act).employee_id, self.employee | self.employee2)
        with self.assertRaises(Exception), self.cr.savepoint(), mute_logger('odoo.sql_db'):
            self.env['td.mebli.accrual'].create({'employee_id': self.employee.id, 'kind': 'crew', 'amount': 1.0,
                                                 'act_id': act.id})
            self.env.flush_all()

    def test_ac_104_default_percent_of_the_company(self):
        self.company.td_crew_pct = 7.5
        order = self._order(terms=False)
        act = self.env['td.mebli.install.act'].create({'task_id': order.tasks_ids.id, 'kind': 'final'})
        self.assertEqual(act.crew_pct, 7.5)

    def test_ac_106_own_lines_and_confirmed_read_only(self):
        Accrual = self.env['td.mebli.accrual']
        mine = Accrual.create({'employee_id': self.employee.id, 'kind': 'bonus', 'amount': 100.0, 'reason': 'Clean site'})
        other = Accrual.create({'employee_id': self.employee2.id, 'kind': 'bonus', 'amount': 100.0, 'reason': 'Clean site'})
        self.assertEqual(Accrual.with_user(self.fitter).search([('id', 'in', (mine | other).ids)]), mine)
        with self.assertRaises(AccessError):
            other.with_user(self.fitter).read(['amount'])
        with self.assertRaises(AccessError):
            mine.with_user(self.fitter).write({'amount': 1000.0})
        mine.action_td_confirm()
        accountant = _user(self.env, 'td_g3_acc', ['account.group_account_user'])
        with self.assertRaises(UserError):
            mine.with_user(accountant).write({'amount': 1.0})
        with self.assertRaises(AccessError):  # only the head cancels
            mine.with_user(accountant).action_td_cancel('Wrong employee')
        head = _user(self.env, 'td_g3_head', ['account.group_account_manager'])
        with self.assertRaises(UserError):
            mine.with_user(head).action_td_cancel(' ')
        mine.with_user(head).action_td_cancel('Wrong employee')
        self.assertEqual(mine.state, 'cancel')
        self.assertEqual(mine.cancel_reason, 'Wrong employee')

    def test_ac_106_accountant_does_not_bypass_the_head_by_rpc(self):
        """CHECKS.md No. 30 (security S-N2): the accountant confirms, but through RPC does not return a confirmed
        accrual to draft (to change its amount), does not cancel it and does not create it cancelled; the head returns
        to draft and cancels with a reason only. No. 31: a confirmed accrual is not deleted (ondelete)."""
        Accrual = self.env['td.mebli.accrual']
        accountant = _user(self.env, 'td_g3_acc2', ['account.group_account_user'])
        line = Accrual.with_user(accountant).create({
            'employee_id': self.employee.id, 'kind': 'bonus', 'amount': 100.0, 'reason': 'Clean site'})
        line.with_user(accountant).write({'state': 'confirmed'})  # the accountant confirms (ACCRUE)
        self.assertEqual(line.state, 'confirmed')
        with self.assertRaises(AccessError):
            line.with_user(accountant).write({'state': 'draft'})
        with self.assertRaises(UserError):
            line.with_user(accountant).write({'amount': 1000.0})
        with self.assertRaises(AccessError):
            line.with_user(accountant).write({'state': 'cancel', 'cancel_reason': 'Mistake'})
        with self.assertRaises(AccessError):
            Accrual.with_user(accountant).create({'employee_id': self.employee.id, 'kind': 'bonus', 'amount': 5.0,
                                                  'reason': 'Clean site', 'state': 'cancel', 'cancel_reason': 'x'})
        with self.assertRaises(UserError):
            line.with_user(accountant).unlink()
        self.assertEqual((line.state, line.amount), ('confirmed', 100.0))
        head = _user(self.env, 'td_g3_head2', ['account.group_account_manager'])
        with self.assertRaises(UserError):  # cancelled by RPC only with a reason
            line.with_user(head).write({'state': 'cancel'})
        line.with_user(head).write({'state': 'draft'})
        line.with_user(head).write({'amount': 120.0})
        line.with_user(accountant).write({'state': 'confirmed'})
        line.with_user(head).write({'state': 'cancel', 'cancel_reason': 'Duplicate'})
        self.assertEqual((line.state, line.amount, line.cancel_reason), ('cancel', 120.0, 'Duplicate'))
        with self.assertRaises(AccessError):  # a cancelled one is not confirmed again by the accountant
            line.with_user(accountant).write({'state': 'confirmed'})
        draft = Accrual.with_user(accountant).create({
            'employee_id': self.employee.id, 'kind': 'bonus', 'amount': 1.0, 'reason': 'Clean site'})
        draft.with_user(accountant).unlink()  # a draft is deleted

    def test_ac_107_master_adds_bonus_in_his_section(self):
        Accrual = self.env['td.mebli.accrual']
        master = _user(self.env, 'td_g3_master', ['mrp.group_mrp_user'])
        section = self.env['hr.department'].create({'name': 'Assembly',
                                                    'manager_id': self.env['hr.employee'].create(
                                                        {'name': 'Master', 'user_id': master.id}).id})
        self.employee.department_id = section
        reason = self.env['td.mebli.accrual.reason'].create({'name': 'Clean site', 'kind': 'bonus', 'default_amount': 200.0})
        bonus = Accrual.with_user(master).create({'employee_id': self.employee.id, 'kind': 'bonus', 'amount': 200.0,
                                                   'reason_id': reason.id})
        self.assertEqual(bonus.state, 'draft')
        self.assertEqual(bonus.author_id, master)
        self.assertEqual(bonus.reason, 'Clean site')
        with self.assertRaises(AccessError):  # not his section
            Accrual.with_user(master).create({'employee_id': self.employee2.id, 'kind': 'penalty', 'amount': -50.0,
                                              'reason_id': reason.id})
        with self.assertRaises(AccessError):  # not a bonus or a penalty
            Accrual.with_user(master).create({'employee_id': self.employee.id, 'kind': 'piece', 'amount': 50.0})
        # A-14 security 2: the master does not confirm his own drafts — neither by the button nor by RPC write
        with self.assertRaises(AccessError):
            bonus.with_user(master).action_td_confirm()
        with self.assertRaises(AccessError):
            bonus.with_user(master).write({'state': 'confirmed'})
        self.assertEqual(bonus.state, 'draft')
        bonus.with_env(self.env).action_td_confirm()  # the head confirms
        with self.assertRaises(UserError):  # AccessError is a UserError too
            bonus.with_user(master).write({'reason': 'Other'})

    def test_ac_108_bonus_without_reason(self):
        Accrual = self.env['td.mebli.accrual']
        with self.assertRaises(ValidationError) as error:
            Accrual.create({'employee_id': self.employee.id, 'kind': 'bonus', 'amount': 100.0})
        self.assertEqual(str(error.exception), "Specify the reason of the bonus or the penalty")
        with self.assertRaises(ValidationError) as error:
            Accrual.with_context(lang='uk_UA').create({'employee_id': self.employee.id, 'kind': 'penalty', 'amount': -1.0})
        self.assertEqual(str(error.exception), "Вкажіть причину премії або штрафу")
        self.assertFalse(Accrual.search([('employee_id', '=', self.employee.id)]))
        line = Accrual.create({'employee_id': self.employee.id, 'kind': 'piece', 'amount': 5.0})
        with self.assertRaises(ValidationError):
            line.write({'kind': 'bonus', 'reason': False})

    def test_ac_134_accruals_sheet(self):
        Accrual = self.env['td.mebli.accrual']
        confirmed = Accrual.create({'employee_id': self.employee.id, 'kind': 'bonus', 'amount': 300.0,
                                    'reason': 'Quick installation', 'date': date(2026, 10, 5)})
        penalty = Accrual.create({'employee_id': self.employee.id, 'kind': 'penalty', 'amount': -100.0,
                                  'reason': 'Late arrival', 'date': date(2026, 10, 6)})
        draft = Accrual.create({'employee_id': self.employee2.id, 'kind': 'bonus', 'amount': 999.0,
                                'reason': 'Draft line', 'date': date(2026, 10, 7)})
        (confirmed | penalty).action_td_confirm()
        html, _kind = self.env['ir.actions.report']._render_qweb_html(
            'td_mebli_install.report_accrual_sheet', (confirmed | penalty | draft).ids)
        text = html.decode()
        for expected in ('Accruals Sheet', 'Fitter One', 'Quick installation', 'Late arrival', 'Bonus', 'Penalty',
                         'Total of the employee', 'Head:', 'td_mebli_report'):
            self.assertIn(expected, text)
        self.assertNotIn('Draft line', text)
        self.assertNotIn('Fitter Two', text)


@tagged('post_install', '-at_install')
class TestNoPieceRateG3(TdMebliSaleCommon):

    def test_ac_105_operation_without_piece_rate(self):
        env = self.env
        env['res.lang']._activate_lang('uk_UA')
        worker = env['hr.employee'].create({'name': 'Worker', 'pin': '3333'})
        order = self._make_order()
        order.action_confirm()
        workorder = order.mrp_production_ids.workorder_ids[:1]
        workorder.operation_id.td_piece_rate = 0.0
        kiosk = env['td.mebli.kiosk']
        kiosk.create({'workorder_id': workorder.id, 'action': 'start', 'employee_id': worker.id, 'pin': '3333'}).action_confirm()
        kiosk.create({'workorder_id': workorder.id, 'action': 'done', 'employee_id': worker.id, 'pin': '3333'}).action_confirm()
        start = datetime(2026, 11, 2, 8, 0)
        workorder.time_ids.write({'date_start': start, 'date_end': start + timedelta(minutes=60)})
        wizard = env['td.mebli.accrual.wizard'].create({'date_from': date(2026, 11, 1), 'date_to': date(2026, 11, 30)})
        wizard.action_accrue()
        self.assertEqual(wizard.missing_rate_count, 1)
        self.assertEqual(wizard.summary, "Without piece rate: 1 operations")
        self.assertIn(workorder.name, wizard.missing_rate_list)
        self.assertFalse(env['td.mebli.accrual'].search([('productivity_id', 'in', workorder.time_ids.ids)]))
        uk = env['td.mebli.accrual.wizard'].with_context(lang='uk_UA').create(
            {'date_from': date(2026, 11, 1), 'date_to': date(2026, 11, 30)})
        uk.action_accrue()
        self.assertEqual(uk.summary, "Без розцінки: 1 операцій")
        # outside the period: nothing listed
        empty = env['td.mebli.accrual.wizard'].create({'date_from': date(2026, 10, 1), 'date_to': date(2026, 10, 31)})
        empty.action_accrue()
        self.assertEqual(empty.missing_rate_count, 0)
