import base64
import json
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

SCHEMA = 'td_mebli_bas/0.1-draft'  # our draft schema until the exchange contract with the franchisee (ВП-1)
SALE_TYPES = ('out_invoice', 'out_refund')
PURCHASE_TYPES = ('in_invoice', 'in_refund')


class TdBasRejected(Exception):
    """BAS rejected the whole batch (AC-040): every document of the batch gets the reason."""


class TdMebliBasChannel(models.Model):
    """Settings of the exchange of one company with its BAS/BAF database (tr/integrations.md §1.2)."""
    _name = 'td.mebli.bas.channel'
    _description = 'BAS Exchange Channel'
    _check_company_auto = True

    name = fields.Char(string='Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company,
                                 index=True)
    transport = fields.Selection([('file', 'File in a Folder / Attachment'), ('http', 'HTTP Service of BAS')],
                                 string='Transport', required=True, default='file')
    endpoint = fields.Char(string='Endpoint', help="Address of the HTTP service of BAS (transport «HTTP»).")
    api_key = fields.Char(string='API Key', groups='base.group_system')
    schema_version = fields.Char(string='Schema Version', default=SCHEMA, readonly=True,
                                 help="Version of our schema of the batch until the exchange contract (ВП-1).")
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user,
                              help="Finance user who gets the activities about the payments not matched.")
    active = fields.Boolean(default=True)
    last_run = fields.Datetime(string='Last Exchange', readonly=True)
    # review A-11: the history before the start of the exchange stays in the old accounting (it is already in BAS)
    start_date = fields.Date(string='Exchange Start Date',
                             help="Documents dated before this day are not sent to BAS (they are already in BAS). "
                                  "Empty — all the posted documents.")
    batch_ids = fields.One2many('td.mebli.bas.batch', 'channel_id', string='Batches')

    @api.constrains('company_id', 'active')
    def _check_one_channel(self):
        for channel in self.filtered('active'):
            if self.search_count([('company_id', '=', channel.company_id.id), ('id', '!=', channel.id)]):
                raise ValidationError(self.env._("A company has one active exchange channel with BAS."))

    @api.model
    def _td_channel_for(self, company):
        channel = self.search([('company_id', '=', company.id)], limit=1)
        if not channel:
            raise UserError(self.env._("No exchange channel with BAS for the company %s.", company.display_name))
        return channel

    # ---------------------------------------------------------------- transport
    def _td_deliver(self, batch, payload):
        """Hands the batch over to BAS. Returns {record key: reason} of the documents BAS rejected; raises TdBasRejected
        when BAS rejects the whole batch. Transport «file»: the file of the batch is the delivery (BAS takes it)."""
        self.ensure_one()
        if self.transport == 'http':
            raise TdBasRejected(self.env._("The HTTP transport waits for the exchange contract with the franchisee."))
        return {}

    def _td_new_batch(self, kind, direction='out'):
        self.ensure_one()
        return self.env['td.mebli.bas.batch'].create({'channel_id': self.id, 'kind': kind, 'direction': direction})

    def _td_attach(self, batch, payload, extension='json'):
        data = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False, indent=1).encode()
        batch.attachment_id = self.env['ir.attachment'].create({
            'name': f"{batch.name.replace('/', '-')}.{extension}", 'raw': data,
            'res_model': batch._name, 'res_id': batch.id})

    def _td_payload(self, batch, records, **extra):
        return {'schema': self.schema_version or SCHEMA, 'batch': batch.name, 'kind': batch.kind,
                'company': {'name': self.company_id.name, 'vat': self.company_id.vat or ''},
                'created': fields.Datetime.to_string(batch.date), **extra, 'records': records}

    def _td_send(self, batch, records, errors, set_state, extra=None):
        """Common part of the outgoing exchange: file, delivery, log, status of the documents. `records` — [(record, data)],
        `errors` — [(record, reason)] found before the delivery; `set_state(records, state, batch)` marks the documents."""
        payload = self._td_payload(batch, [data for _record, data in records], **(extra or {}))
        self._td_attach(batch, payload)
        try:
            rejected = self._td_deliver(batch, payload) or {}
            batch_error = False
        except TdBasRejected as error:
            batch_error = str(error)
            rejected = {data['key']: batch_error for _record, data in records}
        Log = self.env['td.mebli.bas.log']
        sent = []
        for record, reason in errors:
            Log.create({'batch_id': batch.id, 'res_model': record._name, 'res_id': record.id, 'state': 'error',
                        'message': reason})
            set_state(record, 'error', batch)
        for record, data in records:
            if data['key'] in rejected:
                Log.create({'batch_id': batch.id, 'res_model': record._name, 'res_id': record.id, 'state': 'error',
                            'message': self.env._("BAS rejected: %s", rejected[data['key']])})
                set_state(record, 'error', batch)
            else:
                Log.create({'batch_id': batch.id, 'res_model': record._name, 'res_id': record.id, 'state': 'sent',
                            'message': data.get('number') or ''})
                set_state(record, 'sent', batch)
                sent.append(record)
        batch.write({'state': 'error' if batch_error else 'sent', 'message': batch_error,
                     'line_count': len(sent), 'error_count': len(records) + len(errors) - len(sent)})
        self.last_run = fields.Datetime.now()
        return batch

    # ---------------------------------------------------------------- documents (AC-039, AC-040)
    def _td_move_data(self, move):
        company = self.company_id
        partner = move.commercial_partner_id.with_company(company)
        return {
            'key': f'account.move,{move.id}', 'number': move.name, 'type': move.move_type,
            'date': fields.Date.to_string(move.invoice_date or move.date), 'currency': move.currency_id.name,
            'partner': {'code': partner.td_bas_code, 'name': partner.name, 'vat': partner.vat or ''},
            'amount_untaxed': move.amount_untaxed, 'amount_tax': move.amount_tax, 'amount_total': move.amount_total,
            'lines': [{'product_code': line.product_id.with_company(company).td_bas_code or '',
                       'product': line.product_id.display_name or line.name, 'quantity': line.quantity,
                       'price_unit': line.price_unit, 'subtotal': line.price_subtotal}
                      for line in move.invoice_line_ids.filtered(lambda l: l.display_type == 'product')],
        }

    def _td_export_moves(self, moves, kind):
        """Posted invoices of the company into one batch: a document without the BAS code of the partner gets «Exchange
        Error» with the reason, the rest of the batch goes on."""
        self.ensure_one()
        moves = moves.filtered(lambda m: m.state == 'posted' and m.company_id == self.company_id
                               and m.td_bas_state != 'sent')
        if not moves:
            return self.env['td.mebli.bas.batch']
        batch = self._td_new_batch(kind)
        records, errors = [], []
        for move in moves:
            if not move.commercial_partner_id.with_company(self.company_id).td_bas_code:
                errors.append((move, self.env._("The partner %s has no BAS code.", move.commercial_partner_id.name)))
            else:
                records.append((move, self._td_move_data(move)))

        no_code = {move.id for move, _reason in errors}

        def set_state(move, state, batch):
            move.sudo().write({'td_bas_state': state, 'td_bas_batch_id': batch.id,
                               'td_bas_missing_code': state == 'error' and move.id in no_code})
        return self._td_send(batch, records, errors, set_state)

    def _td_moves_to_send(self, move_types, retry_errors=True):
        """Posted documents of the company not sent yet (from the exchange start date). `retry_errors=False` (the daily
        job, review A-11): a document with «Exchange Error» is not sent again every day without a change — only when its
        cause is fixed (the partner got the BAS code); a document rejected by BAS goes again by a button only."""
        self.ensure_one()
        domain = [('company_id', '=', self.company_id.id), ('state', '=', 'posted'), ('move_type', 'in', move_types)]
        if self.start_date:
            domain.append(('date', '>=', self.start_date))
        if retry_errors:
            return self.env['account.move'].search(domain + [('td_bas_state', '!=', 'sent')], order='date, id')
        new = self.env['account.move'].search(domain + [('td_bas_state', '=', False)])
        fixed = self.env['account.move'].search(domain + [('td_bas_state', '=', 'error'), ('td_bas_missing_code', '=', True)])
        fixed = fixed.filtered(lambda m: m.commercial_partner_id.with_company(self.company_id).td_bas_code)
        return (new | fixed).sorted(lambda m: (m.date, m.id))

    def action_td_exchange(self):
        """«Send to BAS» on the channel: sales and purchases of the company, the documents with an error included."""
        return self._td_exchange(retry_errors=True)

    def _td_exchange(self, retry_errors=True):
        batches = self.env['td.mebli.bas.batch']
        for channel in self:
            channel = channel.with_company(channel.company_id)
            batches |= channel._td_export_moves(channel._td_moves_to_send(SALE_TYPES, retry_errors), 'sales')
            batches |= channel._td_export_moves(channel._td_moves_to_send(PURCHASE_TYPES, retry_errors), 'purchases')
            channel.last_run = fields.Datetime.now()
        return batches

    @api.model
    def _td_cron_exchange(self):
        for channel in self.search([]):
            try:
                with self.env.cr.savepoint():
                    channel._td_exchange(retry_errors=False)
            except Exception as error:  # one channel does not stop the others; the error is in the server log
                _logger.exception('td_mebli_bas: exchange of the channel %s failed: %s', channel.name, error)

    # ---------------------------------------------------------------- accruals (AC-109)
    def _td_export_accruals(self, accruals):
        """Confirmed accruals → batch «accruals»: the sheet by employee and kind of accrual."""
        self.ensure_one()
        company = self.company_id
        batch = self._td_new_batch('accruals')
        records, errors, sheet = [], [], {}
        for accrual in accruals:
            code = accrual.employee_id.sudo().with_company(company).td_bas_code
            if not code:
                errors.append((accrual, self.env._("The employee %s has no BAS code.", accrual.employee_id.name)))
                continue
            records.append((accrual, {'key': f'td.mebli.accrual,{accrual.id}', 'number': accrual.order_ref or ''}))
            row = sheet.setdefault((code, accrual.kind), {'employee_code': code, 'employee': accrual.employee_id.name,
                                                          'kind': accrual.kind, 'hours': 0.0, 'amount': 0.0})
            row['hours'] += accrual.hours
            row['amount'] += accrual.amount
        dates = accruals.mapped('date')
        extra = {'period': [fields.Date.to_string(min(dates)), fields.Date.to_string(max(dates))] if dates else [],
                 'sheet': sorted(sheet.values(), key=lambda r: (r['employee'], r['kind']))}

        def set_state(accrual, state, batch):
            accrual.sudo().write({'bas_state': state, 'bas_batch_id': batch.id})
        return self._td_send(batch, records, errors, set_state, extra)

    # ---------------------------------------------------------------- time sheet (AC-078)
    def _td_export_timesheet(self, file_data, filename, line_count):
        self.ensure_one()
        batch = self._td_new_batch('timesheet')
        batch.attachment_id = self.env['ir.attachment'].create({
            'name': filename, 'raw': file_data, 'res_model': batch._name, 'res_id': batch.id})
        try:
            self._td_deliver(batch, file_data)
            batch.write({'state': 'sent', 'line_count': line_count})
        except TdBasRejected as error:
            batch.write({'state': 'error', 'message': str(error)})
        self.last_run = fields.Datetime.now()
        return batch

    # ---------------------------------------------------------------- payments BAS → Odoo (AC-042)
    def _td_import_payments(self, batch):
        """Incoming batch «payments»: a payment of a customer with the number of the invoice → standard payment reconciled
        with the invoice; no such posted invoice — «Not Matched» in the log and an activity to the responsible."""
        self.ensure_one()
        company = self.company_id
        try:
            payload = json.loads(base64.b64decode(batch.attachment_id.datas or b'') or b'{}')
            records = payload['records']
        except (ValueError, KeyError, TypeError) as error:
            batch.write({'state': 'error', 'message': self.env._("The file of the batch is not read: %s", error)})
            return batch
        Log = self.env['td.mebli.bas.log']
        journal = self.env['account.journal'].search([('type', '=', 'bank'), ('company_id', '=', company.id)], limit=1)
        done = unmatched = 0
        batch.log_ids.unlink()  # a repeated import writes the log again; the payments are not doubled (BAS reference)
        failed = 0
        for index, row in enumerate(records, start=1):
            # review A-11: every row in its own savepoint — an error of one payment does not break the batch
            try:
                with self.env.cr.savepoint():
                    result = self._td_import_payment_row(batch, row, company, journal)
            except Exception as error:  # noqa: BLE001 — any error of a row is logged on the row, the batch goes on
                _logger.warning('td_mebli_bas: row %s of the batch %s failed: %s', index, batch.name, error)
                Log.create({'batch_id': batch.id, 'state': 'error', 'message': self.env._(
                    "Row %(row)s (payment %(ref)s): %(error)s", row=index,
                    ref=str((row or {}).get('bas_ref') or '') if isinstance(row, dict) else '', error=error)})
                failed += 1
                continue
            if result == 'unmatched':
                unmatched += 1
            else:
                done += 1
        batch.write({'state': 'accepted', 'line_count': done, 'error_count': unmatched + failed, 'message': False})
        if unmatched:
            batch.activity_schedule(
                'mail.mail_activity_data_todo', user_id=(self.user_id or self.env.user).id,
                summary=self.env._("Payments from BAS not matched: %s", unmatched))
        self.last_run = fields.Datetime.now()
        return batch

    def _td_import_payment_row(self, batch, row, company, journal):
        """One payment of the batch: 'done' (imported or already imported) or 'unmatched'."""
        Log = self.env['td.mebli.bas.log']
        Payment = self.env['account.payment']
        ref, number = str(row.get('bas_ref') or ''), row.get('invoice_number') or ''
        existing = Payment.search([('td_bas_ref', '=', ref), ('company_id', '=', company.id)], limit=1) if ref else Payment
        if existing:
            Log.create({'batch_id': batch.id, 'res_model': 'account.payment', 'res_id': existing.id, 'state': 'sent',
                        'message': self.env._("Already imported: %s", ref)})
            return 'done'
        invoice = self.env['account.move'].search([
            ('company_id', '=', company.id), ('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),
            ('name', '=', number)], limit=1) if number else self.env['account.move']
        if not invoice or invoice.payment_state in ('paid', 'in_payment', 'reversed') or not journal:
            Log.create({'batch_id': batch.id, 'state': 'unmatched', 'message': self.env._(
                "Not matched: payment %(ref)s, amount %(amount)s, invoice «%(number)s».",
                ref=ref, amount=row.get('amount'), number=number)})
            return 'unmatched'
        wizard = self.env['account.payment.register'].with_company(company).with_context(
            active_model='account.move', active_ids=invoice.ids).create({
                'amount': float(row['amount']), 'journal_id': journal.id,
                'payment_date': row.get('date') or fields.Date.context_today(self)})
        payment = wizard._create_payments()
        payment.td_bas_ref = ref
        Log.create({'batch_id': batch.id, 'res_model': 'account.payment', 'res_id': payment.id, 'state': 'sent',
                    'message': self.env._("Payment %(ref)s → invoice %(number)s", ref=ref, number=invoice.name)})
        self._td_after_bas_payment(invoice, payment)
        return 'done'

    def _td_after_bas_payment(self, invoice, payment):
        """Hook after a payment from BAS is reconciled (tr/integrations.md §1.3 п.3, AC-042): the manual payment marks
        of the same order on the same amount (td.mebli.pay.mark, td_mebli_install — a dependency of this module) are
        cancelled."""
        invoice.line_ids.sale_line_ids.order_id._td_cancel_pay_marks(payment.amount)
        return True
