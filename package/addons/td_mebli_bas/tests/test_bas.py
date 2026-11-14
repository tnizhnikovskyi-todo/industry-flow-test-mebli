import base64
import json
from datetime import datetime
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tools.misc import file_path

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.td_mebli_bas.models.bas_channel import TdBasRejected

LOCKED = 'The document has already been sent to BAS — corrections only by a reversal.'


@tagged('post_install', '-at_install')
class TestBasExchange(AccountTestInvoicingCommon):
    """Exchange with BAS (tr/integrations.md §1): our side — batches, log, statuses; the format is the draft (ВП-1)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.finance_group = env.ref('td_mebli_base.group_finance')
        env.user.group_ids |= cls.finance_group | env.ref('hr.group_hr_user') | env.ref('sales_team.group_sale_manager') \
            | env.ref('hr_attendance.group_hr_attendance_manager')
        cls.company = env.company
        cls.channel = env['td.mebli.bas.channel'].create({'name': 'BAS of the company', 'company_id': cls.company.id})
        cls.partner_a.td_bas_code = 'K-0001'
        cls.partner_b.td_bas_code = False
        cls.product_a.td_bas_code = 'N-0001'
        cls.clerk = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Clerk', 'login': 'td_bas_clerk', 'company_id': cls.company.id, 'company_ids': [(6, 0, cls.company.ids)],
            'group_ids': [(6, 0, [env.ref('account.group_account_invoice').id])]})

    def _invoice(self, partner=None, move_type='out_invoice', amount=1000.0):
        return self.init_invoice(move_type, partner=partner or self.partner_a, products=self.product_a,
                                 amounts=[amount], post=True)

    @staticmethod
    def _payload(batch):
        return json.loads(base64.b64decode(batch.attachment_id.datas))

    # ------------------------------------------------------------------ AC-039
    def test_ac_039_daily_exchange_sends_sales_and_purchases(self):
        invoice = self._invoice()
        bill = self._invoice(move_type='in_invoice')
        draft = self.init_invoice('out_invoice', partner=self.partner_a, products=self.product_a)
        cron = self.env.ref('td_mebli_bas.ir_cron_td_bas_exchange')
        self.assertEqual((cron.interval_number, cron.interval_type), (1, 'days'))
        self.env['td.mebli.bas.channel']._td_cron_exchange()
        self.assertEqual((invoice.td_bas_state, bill.td_bas_state), ('sent', 'sent'))
        self.assertFalse(draft.td_bas_state, "a draft is not sent")
        sales = invoice.td_bas_batch_id
        self.assertEqual((sales.kind, sales.state, sales.company_id), ('sales', 'sent', self.company))
        self.assertEqual(sales.line_count, 1)
        self.assertTrue(sales.date)
        payload = self._payload(sales)
        self.assertEqual(payload['schema'], 'td_mebli_bas/0.1-draft')
        record = payload['records'][0]
        self.assertEqual((record['number'], record['partner']['code']), (invoice.name, 'K-0001'))
        self.assertEqual(record['lines'][0]['product_code'], 'N-0001')
        self.assertEqual(bill.td_bas_batch_id.kind, 'purchases')
        self.assertEqual(sales.log_ids.state, 'sent')
        self.assertTrue(self.channel.last_run)
        # the next run does not send the same documents again
        self.assertFalse(self.channel.action_td_exchange())

    def test_ac_039_send_button_on_the_order(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'order_line': [(0, 0, {'product_id': self.product_a.id, 'product_uom_qty': 1, 'price_unit': 500.0})]})
        order.action_confirm()
        self.assertEqual(order.td_bas_state, 'none')
        with self.assertRaises(UserError):  # nothing posted yet
            order.action_td_send_bas()
        invoice = order._create_invoices()
        invoice.action_post()
        order.action_td_send_bas()
        self.assertEqual((invoice.td_bas_state, order.td_bas_state), ('sent', 'sent'))

    def test_ac_039_one_channel_per_company(self):
        with self.assertRaises(ValidationError):
            self.env['td.mebli.bas.channel'].create({'name': 'Second', 'company_id': self.company.id})

    # ------------------------------------------------------------------ AC-040
    def test_ac_040_partner_without_code_is_an_error_the_rest_goes(self):
        good, bad = self._invoice(), self._invoice(partner=self.partner_b)
        batch = self.channel._td_export_moves(good | bad, 'sales')
        self.assertEqual((good.td_bas_state, bad.td_bas_state), ('sent', 'error'))
        self.assertEqual((batch.state, batch.line_count, batch.error_count), ('sent', 1, 1))
        log = batch.log_ids.filtered(lambda l: l.state == 'error')
        self.assertEqual((log.res_model, log.res_id), ('account.move', bad.id))
        self.assertIn(self.partner_b.name, log.message)
        self.assertEqual(log.document, bad.display_name)
        self.assertEqual(len(self._payload(batch)['records']), 1)
        # «Retry» is for the finance user only
        with self.assertRaises(AccessError):
            batch.with_user(self.clerk).action_td_retry()
        self.partner_b.td_bas_code = 'K-0002'
        batch.action_td_retry()
        self.assertEqual(bad.td_bas_state, 'sent')
        self.assertNotEqual(bad.td_bas_batch_id, batch)

    def test_ac_040_bas_rejects_a_document_or_the_batch(self):
        first, second = self._invoice(), self._invoice()
        Channel = type(self.env['td.mebli.bas.channel'])
        with patch.object(Channel, '_td_deliver', return_value={f'account.move,{first.id}': 'unknown contract'}):
            batch = self.channel._td_export_moves(first | second, 'sales')
        self.assertEqual((first.td_bas_state, second.td_bas_state), ('error', 'sent'))
        self.assertIn('unknown contract', batch.log_ids.filtered(lambda l: l.res_id == first.id).message)
        third = self._invoice()
        with patch.object(Channel, '_td_deliver', side_effect=TdBasRejected('schema version')):
            batch = self.channel._td_export_moves(third, 'sales')
        self.assertEqual((batch.state, third.td_bas_state, batch.message), ('error', 'error', 'schema version'))
        # the transport HTTP waits for the contract (ВП-1): the batch is an error, nothing is lost
        self.channel.transport = 'http'
        fourth = self._invoice()
        batch = self.channel._td_export_moves(fourth, 'sales')
        self.assertEqual((batch.state, fourth.td_bas_state), ('error', 'error'))

    # ------------------------------------------------------------------ AC-041
    def test_ac_041_sent_invoice_is_locked_reversal_allowed(self):
        invoice = self._invoice()
        self.channel._td_export_moves(invoice, 'sales')
        total = invoice.amount_total
        with self.assertRaisesRegex(UserError, LOCKED):
            invoice.button_draft()
        with self.assertRaisesRegex(UserError, LOCKED):
            invoice.write({'partner_id': self.partner_b.id})
        with self.assertRaisesRegex(UserError, LOCKED):
            invoice.button_cancel()
        self.assertEqual((invoice.state, invoice.amount_total, invoice.partner_id), ('posted', total, self.partner_a))
        reversal = self.env['account.move.reversal'].with_context(active_model='account.move', active_ids=invoice.ids)\
            .create({'journal_id': invoice.journal_id.id, 'reason': 'storno'})
        reversal.refund_moves()
        refund = self.env['account.move'].search([('reversed_entry_id', '=', invoice.id)])
        self.assertEqual(refund.move_type, 'out_refund')
        invoice.message_post(body='still commentable')  # the chatter is not locked

    def test_ac_041_uk_text_is_the_spec_text(self):
        with open(file_path('td_mebli_bas/i18n/uk.po'), encoding='utf-8') as po:
            self.assertIn('msgstr "Документ уже передано в BAS — виправлення лише сторно"', po.read())

    # ------------------------------------------------------------------ AC-042
    def _incoming(self, records):
        batch = self.env['td.mebli.bas.batch'].create({
            'channel_id': self.channel.id, 'direction': 'in', 'kind': 'payments',
            'file': base64.b64encode(json.dumps({'schema': 'td_mebli_bas/0.1-draft', 'records': records}).encode()),
            'filename': 'payments.json'})
        batch.action_td_import()
        return batch

    def test_ac_042_payment_from_bas_reconciles_the_invoice(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'order_line': [(0, 0, {'product_id': self.product_a.id, 'product_uom_qty': 1, 'price_unit': 1000.0})]})
        order.action_confirm()
        invoice = order._create_invoices()
        invoice.action_post()
        self.channel._td_export_moves(invoice, 'sales')  # sent to BAS before the payment: the payment still reconciles
        received = order.td_pay_received
        rows = [{'bas_ref': 'P-1', 'date': '2026-11-10', 'amount': invoice.amount_total, 'invoice_number': invoice.name},
                {'bas_ref': 'P-2', 'date': '2026-11-10', 'amount': 10.0, 'invoice_number': 'NO/SUCH/1'}]
        batch = self._incoming(rows)
        self.assertEqual((batch.state, batch.line_count, batch.error_count), ('accepted', 1, 1))
        self.assertIn(invoice.payment_state, ('paid', 'in_payment'))
        payment = self.env['account.payment'].search([('td_bas_ref', '=', 'P-1')])
        self.assertEqual(len(payment), 1)
        self.assertIn(invoice, payment.invoice_ids)
        order.invalidate_recordset()
        self.assertAlmostEqual(order.td_pay_received, received + invoice.amount_total, msg="«Received» of the order")
        unmatched = batch.log_ids.filtered(lambda l: l.state == 'unmatched')
        self.assertIn('NO/SUCH/1', unmatched.message)
        self.assertTrue(batch.activity_ids, "the responsible gets an activity about the payment not matched")
        # the import again (Retry) does not double the payment
        batch.action_td_retry()
        self.assertEqual(self.env['account.payment'].search_count([('td_bas_ref', '=', 'P-1')]), 1)

    def test_ac_042_payment_from_bas_cancels_manual_marks(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'order_line': [(0, 0, {'product_id': self.product_a.id, 'product_uom_qty': 1, 'price_unit': 1000.0})]})
        order.action_confirm()
        other = order.copy()
        other.action_confirm()
        invoice = order._create_invoices()
        invoice.action_post()
        Mark = self.env['td.mebli.pay.mark']
        mark = Mark.create({'order_id': order.id, 'amount': invoice.amount_total, 'reason': 'Bank transfer seen'})
        other_amount = Mark.create({'order_id': order.id, 'amount': 77.0, 'reason': 'Cash at the office'})
        other_mark = Mark.create({'order_id': other.id, 'amount': invoice.amount_total, 'reason': 'Other order'})
        self._incoming([{'bas_ref': 'P-M1', 'date': '2026-11-10', 'amount': invoice.amount_total,
                         'invoice_number': invoice.name}])
        self.assertTrue(mark.cancelled, "the mark of the paid order on the same amount is cancelled")
        self.assertTrue(mark.exists(), "cancelled, not deleted")
        self.assertFalse(other_amount.cancelled, "a mark of another amount stays (tr/integrations.md §1.3 п.3)")
        self.assertFalse(other_mark.cancelled, "the marks of another order stay")

    def test_ac_042_broken_file_is_a_batch_error(self):
        batch = self.env['td.mebli.bas.batch'].create({
            'channel_id': self.channel.id, 'direction': 'in', 'kind': 'payments',
            'file': base64.b64encode(b'not json'), 'filename': 'payments.json'})
        batch.action_td_import()
        self.assertEqual(batch.state, 'error')
        self.assertTrue(batch.message)

    def test_ac_042_bad_row_does_not_break_the_batch(self):
        """Review A-11: every row in its own savepoint — a row with a broken amount is an error of the row, the
        good payment of the same batch is imported."""
        invoice = self._invoice()
        rows = [{'bas_ref': 'P-B1', 'date': '2026-11-10', 'amount': 'not a number', 'invoice_number': invoice.name},
                {'bas_ref': 'P-B2', 'date': '2026-11-10', 'amount': invoice.amount_total, 'invoice_number': invoice.name}]
        batch = self._incoming(rows)
        self.assertEqual((batch.state, batch.line_count, batch.error_count), ('accepted', 1, 1))
        self.assertEqual(self.env['account.payment'].search_count([('td_bas_ref', '=', 'P-B2')]), 1)
        self.assertFalse(self.env['account.payment'].search_count([('td_bas_ref', '=', 'P-B1')]))
        error = batch.log_ids.filtered(lambda l: l.state == 'error')
        self.assertIn('Row 1', error.message)

    def test_ac_039_start_date_and_errors_not_repeated_daily(self):
        """Review A-11: the history before the exchange start date is not sent; a document with «Exchange Error» is
        not sent again by the daily job without a change — after the fix (the BAS code) or by the button only."""
        old = self.init_invoice('out_invoice', partner=self.partner_a, products=self.product_a, amounts=[100.0],
                                post=True, invoice_date='2018-01-31')
        self.channel.start_date = '2018-06-01'  # the other invoices of the test are of 2019
        bad = self._invoice(partner=self.partner_b)
        Channel = self.env['td.mebli.bas.channel']
        Channel._td_cron_exchange()
        self.assertFalse(old.td_bas_state, "the history before the start date stays out of the exchange")
        self.assertEqual(bad.td_bas_state, 'error')
        batch = bad.td_bas_batch_id
        Channel._td_cron_exchange()  # the next day, nothing changed: no new batch, no new error
        self.assertEqual(bad.td_bas_batch_id, batch)
        self.partner_b.td_bas_code = 'K-0003'  # the cause is fixed: the daily job sends it
        Channel._td_cron_exchange()
        self.assertEqual(bad.td_bas_state, 'sent')
        # a document rejected by BAS waits for the button
        rejected = self._invoice()
        with patch.object(type(Channel), '_td_deliver', return_value={f'account.move,{rejected.id}': 'contract'}):
            Channel._td_cron_exchange()
        self.assertEqual(rejected.td_bas_state, 'error')
        first = rejected.td_bas_batch_id
        Channel._td_cron_exchange()
        self.assertEqual(rejected.td_bas_batch_id, first)
        self.channel.action_td_exchange()  # «Send to BAS» on the channel retries it
        self.assertEqual(rejected.td_bas_state, 'sent')

    # ------------------------------------------------------------------ AC-078
    def test_ac_078_time_sheet_batch_with_the_bas_code(self):
        env = self.env
        env.user.tz = 'Europe/Kyiv'
        worker = env['hr.employee'].create({'name': 'Cutter BAS', 'barcode': '0007'})
        worker.td_bas_code = 'T-77'
        env['hr.attendance'].create({'employee_id': worker.id, 'check_in': datetime(2026, 11, 3, 6, 0),
                                     'check_out': datetime(2026, 11, 3, 10, 0)})
        wizard = env['td.mebli.timesheet.export'].create({'date_from': '2026-11-01', 'date_to': '2026-11-30'})
        with self.assertRaises(UserError):
            wizard.action_td_send_bas()  # no file yet
        wizard.action_build()
        text = base64.b64decode(wizard.file).decode('utf-8-sig')
        self.assertIn(';T-77;', text, "the external code of BAS is the personnel code of the file")
        action = wizard.action_td_send_bas()
        batch = env['td.mebli.bas.batch'].browse(action['res_id'])
        self.assertEqual((batch.kind, batch.state, batch.line_count), ('timesheet', 'sent', 1))
        self.assertEqual(batch.attachment_id.raw.decode('utf-8-sig'), text)

    # ------------------------------------------------------------------ AC-109
    def test_ac_109_confirmed_accruals_into_the_sheet(self):
        env = self.env
        coded = env['hr.employee'].create({'name': 'Fitter A'})
        coded.td_bas_code = 'E-1'
        nameless = env['hr.employee'].create({'name': 'Fitter B'})
        Accrual = env['td.mebli.accrual']
        bonus = Accrual.create({'employee_id': coded.id, 'kind': 'bonus', 'amount': 300.0, 'reason': 'Quality'})
        bonus2 = Accrual.create({'employee_id': coded.id, 'kind': 'bonus', 'amount': 200.0, 'reason': 'Speed'})
        penalty = Accrual.create({'employee_id': coded.id, 'kind': 'penalty', 'amount': -50.0, 'reason': 'Late'})
        other = Accrual.create({'employee_id': nameless.id, 'kind': 'bonus', 'amount': 100.0, 'reason': 'Help'})
        draft = Accrual.create({'employee_id': coded.id, 'kind': 'bonus', 'amount': 999.0, 'reason': 'Draft'})
        (bonus | bonus2 | penalty | other).action_td_confirm()
        batches = (bonus | bonus2 | penalty | other | draft).action_td_send_bas()
        self.assertEqual(len(batches), 1)
        self.assertEqual((batches.kind, batches.line_count, batches.error_count), ('accruals', 3, 1))
        sheet = {(row['employee_code'], row['kind']): row['amount'] for row in self._payload(batches)['sheet']}
        self.assertEqual(sheet, {('E-1', 'bonus'): 500.0, ('E-1', 'penalty'): -50.0})
        self.assertEqual((bonus.bas_state, other.bas_state, draft.bas_state), ('sent', 'error', False))
        with self.assertRaisesRegex(UserError, LOCKED):
            bonus.write({'reason': 'Changed'})
        with self.assertRaises(UserError):  # a confirmed accrual (td_mebli_install) sent to BAS is not deleted
            bonus.unlink()
        self.assertTrue(bonus.exists())
        # review A-14 L-1: the lock of BAS is an `ondelete` check that does not block the uninstallation of the module
        with self.assertRaisesRegex(UserError, LOCKED):
            bonus._unlink_except_sent_to_bas()
        ondelete = [m for m in env['td.mebli.accrual']._ondelete_methods
                    if m.__name__ == '_unlink_except_sent_to_bas']
        self.assertEqual(len(ondelete), 1)
        self.assertFalse(ondelete[0]._ondelete)
        draft.unlink()  # not sent to BAS: deleted as before
        self.assertFalse(draft.exists())
        with self.assertRaises(UserError):
            bonus.action_td_send_bas()  # already sent: nothing to send
