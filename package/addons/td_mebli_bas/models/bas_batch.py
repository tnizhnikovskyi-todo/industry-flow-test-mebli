from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

KINDS = [('catalog', 'Catalogs'), ('sales', 'Sales'), ('purchases', 'Purchases'), ('payments', 'Payments'),
         ('accruals', 'Accruals'), ('timesheet', 'Time Sheet')]


class TdMebliBasBatch(models.Model):
    """Exchange batch (tr/integrations.md §1.2): one file of one kind, out (Odoo → BAS) or in (BAS → Odoo)."""
    _name = 'td.mebli.bas.batch'
    _description = 'BAS Exchange Batch'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Batch', required=True, readonly=True, copy=False, default='/')
    channel_id = fields.Many2one('td.mebli.bas.channel', string='Channel', required=True, ondelete='restrict', index=True)
    company_id = fields.Many2one(related='channel_id.company_id', store=True, string='Company', index=True)
    direction = fields.Selection([('out', 'Odoo → BAS'), ('in', 'BAS → Odoo')], string='Direction', required=True,
                                 default='out')
    kind = fields.Selection(KINDS, string='Kind', required=True)
    state = fields.Selection([('draft', 'Draft'), ('sent', 'Sent'), ('accepted', 'Accepted'), ('error', 'Error')],
                             string='Status', default='draft', required=True, tracking=True)
    attachment_id = fields.Many2one('ir.attachment', string='File', readonly=True, copy=False)
    file = fields.Binary(string='Upload File', attachment=False,
                         help="Incoming batch: the file from BAS (draft JSON schema until the contract, ВП-1).")
    filename = fields.Char(string='File Name')
    line_count = fields.Integer(string='Documents', readonly=True)
    error_count = fields.Integer(string='Errors', readonly=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True, readonly=True)
    message = fields.Text(string='Batch Error', readonly=True)
    log_ids = fields.One2many('td.mebli.bas.log', 'batch_id', string='Log')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('td.mebli.bas.batch') or '/'
        return super().create(vals_list)

    def _td_check_finance(self):
        if not self.env.su and not self.env.user.has_group('td_mebli_base.group_finance'):
            raise AccessError(self.env._("Only the finance users run the exchange with BAS."))

    def action_td_import(self):
        """Incoming batch: reads the uploaded file of BAS (payments)."""
        self._td_check_finance()
        for batch in self:
            if batch.direction != 'in' or batch.kind != 'payments':
                raise UserError(self.env._("Only an incoming batch of payments is imported."))
            if batch.file:
                batch.attachment_id = self.env['ir.attachment'].create({
                    'name': batch.filename or f'{batch.name}.json', 'datas': batch.file,
                    'res_model': batch._name, 'res_id': batch.id})
                batch.file = False
            if not batch.attachment_id:
                raise UserError(self.env._("Upload the file of the batch first."))
            batch.channel_id._td_import_payments(batch)
        return True

    def action_td_retry(self):
        """«Retry» (finance, AC-040): the documents with an error go into a new batch; an incoming batch is read again."""
        self._td_check_finance()
        new = self.browse()
        for batch in self:
            channel = batch.channel_id.with_company(batch.company_id)
            if batch.direction == 'in':
                channel._td_import_payments(batch)
                new |= batch
                continue
            failed = batch.log_ids.filtered(lambda l: l.state == 'error')
            moves = self.env['account.move'].browse(failed.filtered(lambda l: l.res_model == 'account.move').mapped('res_id'))
            accruals = self.env['td.mebli.accrual'].browse(
                failed.filtered(lambda l: l.res_model == 'td.mebli.accrual').mapped('res_id'))
            if moves.exists():
                new |= channel._td_export_moves(moves.exists(), batch.kind)
            if accruals.exists():
                new |= channel._td_export_accruals(accruals.exists().filtered(lambda a: a.bas_state != 'sent'))
        if not new:
            raise UserError(self.env._("Nothing to retry: the batch has no documents with an error."))
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'view_mode': 'list,form',
                'domain': [('id', 'in', new.ids)], 'name': self.env._("Exchange Batches")}


class TdMebliBasLog(models.Model):
    """Line of the exchange log: one document of a batch and its result."""
    _name = 'td.mebli.bas.log'
    _description = 'BAS Exchange Log'
    _order = 'id desc'

    batch_id = fields.Many2one('td.mebli.bas.batch', string='Batch', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='batch_id.company_id', store=True, string='Company')
    date = fields.Datetime(related='batch_id.date', string='Date')
    res_model = fields.Char(string='Document Model', readonly=True)
    res_id = fields.Many2oneReference(string='Document ID', model_field='res_model', readonly=True)
    document = fields.Char(string='Document', compute='_compute_document')
    state = fields.Selection([('sent', 'Sent'), ('error', 'Error'), ('unmatched', 'Not Matched')], string='Result',
                             required=True)
    message = fields.Text(string='Message')

    @api.depends('res_model', 'res_id')
    def _compute_document(self):
        for line in self:
            record = self.env[line.res_model].browse(line.res_id).exists() if line.res_model and line.res_id else False
            line.document = record.display_name if record else ''
