from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

# AC-104/107: the head confirms the drafts and accrues — the production manager or the accountant; the accounting
# administrator does the same as the accountant (CHECKS.md No. 35: in Odoo 19 account.group_account_manager does not
# imply account.group_account_user, account/security/account_security.xml)
ACCRUE_GROUPS = ('mrp.group_mrp_manager', 'account.group_account_user', 'account.group_account_manager')
# AC-106: the head who confirms the accruals cancels a confirmed line (with a reason): production or accounting manager
CANCEL_GROUPS = ('mrp.group_mrp_manager', 'account.group_account_manager')
# CHECKS.md No. 36: the reason of the cancellation and the author are fixed as well (written by `action_td_cancel` only)
LOCKED = ('employee_id', 'date', 'kind', 'hours', 'piece_rate', 'amount', 'reason', 'reason_id', 'productivity_id',
          'act_id', 'company_id', 'cancel_reason', 'author_id')


class TdMebliAccrualReason(models.Model):
    """AC-107: the list of the reasons of the bonuses and the penalties (the typical set is data of the config package)."""
    _name = 'td.mebli.accrual.reason'
    _description = 'Reason of a Bonus or a Penalty'
    _order = 'kind, name'

    name = fields.Char(string='Reason', required=True, translate=True)
    kind = fields.Selection([('bonus', 'Bonus'), ('penalty', 'Penalty')], string='Kind', required=True)
    default_amount = fields.Monetary(string='Default Amount')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', compute='_compute_currency_id')
    active = fields.Boolean(default=True)

    @api.depends('company_id')
    def _compute_currency_id(self):
        for reason in self:
            reason.currency_id = (reason.company_id or self.env.company).currency_id


class TdMebliAccrual(models.Model):
    _name = 'td.mebli.accrual'
    _description = 'Accrual to a Worker or a Crew'
    _order = 'date desc, id desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, index=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    kind = fields.Selection([('piece', 'Piecework'), ('crew', 'Crew Percent'), ('bonus', 'Bonus'), ('penalty', 'Penalty')],
                            string='Kind', required=True)
    # a copy of the duration of the time line of the tablet (piecework): set by «Accrue», never typed by hand
    hours = fields.Float(string='Hours', digits=(16, 2), readonly=True)
    piece_rate = fields.Monetary(string='Piece Rate', readonly=True)
    amount = fields.Monetary(string='Amount', required=True)
    reason_id = fields.Many2one('td.mebli.accrual.reason', string='Reason', index='btree_not_null',
                                domain="[('kind', '=', kind)]")
    reason = fields.Char(string='Comment')
    productivity_id = fields.Many2one('mrp.workcenter.productivity', string='Time Line', ondelete='set null', readonly=True)
    workcenter_id = fields.Many2one(related='productivity_id.workcenter_id', store=True, string='Work Center')
    act_id = fields.Many2one('td.mebli.install.act', string='Act', ondelete='set null', readonly=True)
    order_ref = fields.Char(string='Order', compute='_compute_order_ref', store=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one(related='company_id.currency_id')
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('cancel', 'Cancelled')],
                             string='Status', default='draft')
    author_id = fields.Many2one('res.users', string='Author', default=lambda self: self.env.user, readonly=True)
    cancel_reason = fields.Char(string='Cancellation Reason', readonly=True, copy=False)

    # review A-11: «Accrue» twice (two users at once, or a retry) never makes a second live accrual of the same time
    # line or of the same installer of the same act; a cancelled accrual does not count
    _unique_piece = models.UniqueIndex(
        "(productivity_id) WHERE state != 'cancel' AND productivity_id IS NOT NULL",
        'The time line is already accrued.')
    _unique_crew = models.UniqueIndex(
        "(act_id, employee_id) WHERE state != 'cancel' AND act_id IS NOT NULL",
        'The crew percent of this act is already accrued to this employee.')

    _reason_required = models.Constraint(
        "CHECK(kind NOT IN ('bonus', 'penalty') OR reason IS NOT NULL)",
        'A bonus or a penalty needs a reason.')

    @api.depends('productivity_id.production_id.origin', 'act_id.order_id.name')
    def _compute_order_ref(self):
        for accrual in self:
            accrual.order_ref = accrual.act_id.order_id.name or accrual.productivity_id.production_id.origin or ''

    @api.onchange('reason_id')
    def _onchange_reason_id(self):
        if self.reason_id and not self.amount and self.reason_id.default_amount:
            sign = -1 if self.kind == 'penalty' else 1
            self.amount = sign * abs(self.reason_id.default_amount)

    def _td_prepare_reason(self, vals, kind):
        """AC-108: a bonus or a penalty needs a reason (the error of SPEC); the comment keeps the name of the reason."""
        if kind not in ('bonus', 'penalty'):
            return vals
        reason = self.env['td.mebli.accrual.reason'].browse(vals['reason_id']) if vals.get('reason_id') else False
        if not reason and not (vals.get('reason') or '').strip():
            raise ValidationError(self.env._("Specify the reason of the bonus or the penalty"))
        if reason and not (vals.get('reason') or '').strip():
            # sudo: read only: the name of the reason is copied to the accrual for any author
            vals['reason'] = reason.sudo().name
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [self._td_prepare_reason(dict(vals), vals.get('kind')) for vals in vals_list]
        for vals in vals_list:
            if vals.get('state', 'draft') != 'draft':
                self.browse()._td_check_state_change(vals)
        return super().create(vals_list)

    def _td_check_state_change(self, vals):
        """AC-106 (CHECKS.md No. 30, 35), also through RPC and for the head: the only changes of the state are
        draft → confirmed (ACCRUE_GROUPS) and draft or confirmed → cancelled (CANCEL_GROUPS, with a reason).
        A confirmed accrual is never returned to draft and a cancelled one is never restored (superuser only)."""
        if self.env.su:
            return
        state = vals['state']
        if state == 'confirmed':
            if any(accrual.state == 'cancel' for accrual in self):
                raise AccessError(self.env._("A confirmed or cancelled accrual is read-only: the head only cancels it "
                                             "with a reason."))
            self._td_check_confirm_rights()
            return
        if state == 'draft':
            if any(accrual.state != 'draft' for accrual in self):
                raise AccessError(self.env._("A confirmed or cancelled accrual is read-only: the head only cancels it "
                                             "with a reason."))
            return
        # cancel
        if not any(self.env.user.has_group(group) for group in CANCEL_GROUPS):
            raise AccessError(self.env._("A confirmed accrual is cancelled by the head only."))
        if not self or any(accrual.state == 'cancel' for accrual in self):  # created cancelled / the reason rewritten
            raise AccessError(self.env._("A confirmed or cancelled accrual is read-only: the head only cancels it "
                                         "with a reason."))
        if not (vals.get('cancel_reason') or '').strip():
            raise UserError(self.env._("Specify the reason of the cancellation"))

    def write(self, vals):
        # A-14 security 2: the state (confirm / cancel) is changed by the head only, also through RPC — the shop master
        # writes the drafts of his section (record rule) but does not confirm his own bonuses and penalties
        if 'state' in vals:
            self._td_check_state_change(vals)
        if 'hours' in vals and not self.env.su:
            raise UserError(self.env._("The hours of an accrual are the time of the tablet: they are not changed by hand."))
        # a confirmed accrual is handed over to the accounting: its figures are fixed
        locked = set(vals) & set(LOCKED)
        if vals.get('state') == 'cancel':
            locked.discard('cancel_reason')  # the cancellation itself, checked by _td_check_state_change
        if locked and not self.env.su and any(a.state in ('confirmed', 'cancel') for a in self):
            raise UserError(self.env._("A confirmed accrual cannot be changed: add a new bonus or penalty instead."))
        if {'kind', 'reason_id', 'reason'} & set(vals):
            for accrual in self:
                checked = dict(vals)
                checked.setdefault('reason_id', accrual.reason_id.id)
                checked.setdefault('reason', accrual.reason)
                self._td_prepare_reason(checked, vals.get('kind', accrual.kind))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_confirmed(self):
        # CHECKS.md No. 31 (lint E8140): the check is not run when the module is uninstalled
        if not self.env.su and any(a.state in ('confirmed', 'cancel') for a in self):
            raise UserError(self.env._("A confirmed accrual cannot be deleted."))

    def action_td_confirm(self):
        self._td_check_confirm_rights()
        self.filtered(lambda a: a.state == 'draft').write({'state': 'confirmed'})
        return True

    def action_td_cancel(self, reason):
        """AC-106: only the head (production or accounting manager) cancels a confirmed accrual, with a reason."""
        if not (self.env.su or any(self.env.user.has_group(group) for group in CANCEL_GROUPS)):
            raise AccessError(self.env._("A confirmed accrual is cancelled by the head only."))
        if not (reason or '').strip():
            raise UserError(self.env._("Specify the reason of the cancellation"))
        # sudo: the head is checked above (CANCEL_GROUPS); a confirmed line is locked for every user
        self.filtered(lambda a: a.state == 'confirmed').sudo().write({'state': 'cancel', 'cancel_reason': reason.strip()})
        return True

    def action_td_cancel_wizard(self):
        return {'type': 'ir.actions.act_window', 'name': self.env._("Cancel Accruals"),
                'res_model': 'td.mebli.accrual.cancel', 'view_mode': 'form', 'target': 'new',
                'context': {'default_accrual_ids': self.ids}}

    @api.model
    def _td_check_confirm_rights(self):
        """AC-106: the accruals are confirmed by the head (the shop manager or the accountant), checked on the server."""
        if not (self.env.su or any(self.env.user.has_group(group) for group in ACCRUE_GROUPS)):
            raise AccessError(self.env._("Accruals are confirmed by the shop manager or the accountant."))

    @api.model
    def _td_check_accrue_rights(self):
        if not (self.env.su or any(self.env.user.has_group(group) for group in ACCRUE_GROUPS)):
            raise AccessError(self.env._("Accruals are made by the shop manager or the accountant."))

    @api.model
    def _td_accrue(self, date_from=False, date_to=False):
        """Piecework from the time lines of the tablet on done work orders (the piece rate of the operation) and the
        crew percent from the signed acts that have no accrual yet; bonuses and penalties are entered by hand.
        The shop manager and the accountant accrue; the time lines and the acts are read as the system (the accountant
        has no manufacturing rights), the accruals are created as the user.

        Returns (accruals, work orders without a piece rate) of the period (AC-105: no line, listed in the summary)."""
        self._td_check_accrue_rights()
        company = self.env.company
        start = fields.Datetime.to_datetime(date_from) if date_from else False
        end = fields.Datetime.to_datetime(date_to) + timedelta(days=1) if date_to else False
        vals = []
        # piecework (decision AI-08): the piece rate of the operation × its basis quantity on the BoM of the order
        # × the produced quantity of a done work order, shared between the workers of the tablet by their time
        domain = [('td_employee_id', '!=', False), ('date_end', '!=', False), ('loss_type', '=', 'productive'),
                  ('company_id', '=', company.id), ('workorder_id.state', '=', 'done')]
        if start:
            domain.append(('date_end', '>=', start))
        if end:
            domain.append(('date_end', '<', end))
        # sudo: rights checked by _td_check_accrue_rights; the accountant reads the time lines of manufacturing
        all_lines = self.env['mrp.workcenter.productivity'].sudo().search(domain)
        lines = all_lines.filtered(lambda line: line.workorder_id.operation_id.td_piece_rate > 0)
        no_rate = (all_lines - lines).workorder_id
        # sudo: duplicates are searched among all the accruals, not only the ones the user reads
        done = set(self.sudo().search([('productivity_id', 'in', lines.ids), ('state', '!=', 'cancel')]).productivity_id.ids)
        for workorder, wo_lines in lines.grouped('workorder_id').items():
            operation = workorder.operation_id
            if not workorder.qty_produced:  # nothing produced: no piecework (not «one piece» by default)
                continue
            total = round(operation.td_piece_rate * operation._td_basis_quantity() * workorder.qty_produced, 2)
            minutes = sum(wo_lines.mapped('duration'))
            for line in wo_lines.filtered(lambda line: line.id not in done):
                share = line.duration / minutes if minutes else 1.0 / len(wo_lines)
                vals.append({'employee_id': line.td_employee_id.id, 'date': fields.Date.context_today(self, line.date_end),
                             'kind': 'piece', 'hours': line.duration / 60.0, 'amount': round(total * share, 2),
                             'piece_rate': operation.td_piece_rate, 'productivity_id': line.id,
                             'reason': workorder.name, 'company_id': company.id})
        # the crew percent (VP-15): the signed acts with a crew amount — the final act, or every stage «By stages»
        act_domain = [('state', '=', 'signed'), ('crew_amount', '>', 0), ('order_id.company_id', '=', company.id)]
        if start:
            act_domain.append(('signed_on', '>=', start))
        if end:
            act_domain.append(('signed_on', '<', end))
        # sudo: rights checked by _td_check_accrue_rights; the acts are read in all the visits of the company
        acts = self.env['td.mebli.install.act'].sudo().search(act_domain)
        # sudo: duplicates are searched among all the accruals, not only the ones the user reads
        accrued = set(self.sudo().search([('act_id', 'in', acts.ids), ('state', '!=', 'cancel')]).act_id.ids)
        for act in acts.filtered(lambda a: a.id not in accrued):
            # review A-11: a user has an employee in every company — only the employees of the company of the act
            crew = act.crew_user_ids.employee_ids.filtered(lambda e: e.company_id == company)
            for employee, share in act._td_crew_split(crew).items():  # VP-14: equally or by the hours of the act
                vals.append({'employee_id': employee.id, 'date': fields.Date.context_today(self, act.signed_on),
                             'kind': 'crew', 'amount': round(act.crew_amount * share, 2), 'act_id': act.id,
                             'reason': act.name, 'company_id': company.id})
        return self.create(vals), no_rate

    @api.model
    def action_td_accrue(self):
        """Accrue everything not accrued yet (no period). The button of the list opens the wizard of the period
        (`action_td_accrue_wizard`, AC-105: the summary lists the operations without a piece rate)."""
        self._td_accrue()
        return {'type': 'ir.actions.client', 'tag': 'soft_reload'}

    @api.model
    def action_td_accrue_wizard(self):
        self._td_check_accrue_rights()
        return {'type': 'ir.actions.act_window', 'name': self.env._("Accrue"),
                'res_model': 'td.mebli.accrual.wizard', 'view_mode': 'form', 'target': 'new'}


class TdMebliAccrualWizard(models.TransientModel):
    """AC-104/105: «Accrue» for a period; the summary shows «Without piece rate: N operations» with the list."""
    _name = 'td.mebli.accrual.wizard'
    _description = 'Accrue for a Period'

    date_from = fields.Date(string='From', required=True,
                            default=lambda self: fields.Date.context_today(self).replace(day=1))
    date_to = fields.Date(string='To', required=True, default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)
    state = fields.Selection([('draft', 'Period'), ('done', 'Summary')], default='draft')
    accrual_count = fields.Integer(string='Accruals Created', readonly=True)
    missing_rate_count = fields.Integer(string='Without Piece Rate', readonly=True)
    # names, not a link: the accountant has no manufacturing rights to open the work orders
    missing_rate_list = fields.Text(string='Operations without a Piece Rate', readonly=True)
    summary = fields.Char(string='Summary', readonly=True)

    def action_accrue(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(self.env._("The start of the period is after its end."))
        accruals, no_rate = self.env['td.mebli.accrual'].with_company(self.company_id)._td_accrue(
            self.date_from, self.date_to)
        # sudo: read only: the names of the work orders without a piece rate for the result message
        no_rate_names = [f"{wo.production_id.name} · {wo.name} · {wo.workcenter_id.name}" for wo in no_rate.sudo()]
        self.write({'state': 'done', 'accrual_count': len(accruals), 'missing_rate_count': len(no_rate),
                    'missing_rate_list': '\n'.join(no_rate_names),
                    'summary': self.env._("Without piece rate: %(count)s operations", count=len(no_rate))})
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': self.id, 'view_mode': 'form',
                'target': 'new', 'name': self.env._("Accrue")}


class TdMebliAccrualCancel(models.TransientModel):
    _name = 'td.mebli.accrual.cancel'
    _description = 'Cancel Confirmed Accruals'

    accrual_ids = fields.Many2many('td.mebli.accrual', string='Accruals')
    reason = fields.Char(string='Reason', required=True)

    def action_cancel(self):
        self.ensure_one()
        self.accrual_ids.action_td_cancel(self.reason)
        return {'type': 'ir.actions.act_window_close'}
