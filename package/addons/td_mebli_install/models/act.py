from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class TdMebliInstallAct(models.Model):
    _name = 'td.mebli.install.act'
    _description = 'Installation Act'
    _inherit = ['mail.thread']
    _order = 'id desc'
    _mail_post_access = 'read'  # a signed act is read only (record rule), the crew still writes in its chatter

    name = fields.Char(string='Number', required=True, readonly=True, copy=False, default='/')
    task_id = fields.Many2one('project.task', string='Visit', required=True, ondelete='cascade', index=True)
    order_id = fields.Many2one(related='task_id.sale_order_id', store=True, string='Order', index=True)
    company_id = fields.Many2one(related='task_id.company_id', store=True, string='Company', index=True)
    crew_user_ids = fields.Many2many(related='task_id.user_ids', string='Crew')
    kind = fields.Selection([('stage', 'Stage Act'), ('final', 'Final Act')], string='Kind', required=True,
                            default='final', tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('signed', 'Signed')], string='Status', default='draft',
                             tracking=True, copy=False)
    signature = fields.Image(string='Signature of the Customer', copy=False, max_width=1024, max_height=512)
    signed_by = fields.Char(string='Signed by', copy=False)
    signed_on = fields.Datetime(string='Signed on', readonly=True, copy=False)
    checklist = fields.Text(string='Checklist', default=lambda self: self.env.company.td_act_checklist or self.env._(
        "Fronts adjusted\nGaps are even\nAppliances connected by the customer's technician\nWorkplace cleaned"))
    defect_ids = fields.One2many('td.mebli.install.defect', 'act_id', string='Defects')
    defect_open_count = fields.Integer(string='Open Defects', compute='_compute_defects')
    photo_ids = fields.Many2many('ir.attachment', string='Photos')
    photo_archive = fields.Boolean(string='In the Photo Archive', copy=False,
                                   help='The photos may be used for advertising (only with the consent of the customer).')
    photo_consent = fields.Boolean(
        string='Customer Consents to Publish the Photos', copy=False,
        help="Marked by the crew from the words of the customer (or by the contract) before the signature; without it "
             "the photos do not go to the photo archive (AC-100).")
    crew_pct = fields.Float(string='Crew, %', digits=(5, 2), default=lambda self: self.env.company.td_crew_pct,
                            help='Share of the order amount (without taxes) paid to the crew for the installation '
                                 '(default: the percent of the company).')
    crew_base = fields.Selection(related='company_id.td_crew_base', string='Crew Percent Base')
    stage_pct = fields.Float(
        string='Share of the Work, %', digits=(5, 2), default=0.0,
        help="Crew percent «By stages» (VP-15): the share of the order work done at this stage; the final act gets the "
             "rest of 100 %.")
    crew_line_ids = fields.One2many('td.mebli.install.act.crew', 'act_id', string='Crew Hours',
                                    help="Hours of every installer at the visit: the crew percent «By time» (VP-14).")
    currency_id = fields.Many2one(related='order_id.currency_id')
    # fixed at the signature: a later change of the order does not change the amount of a signed act
    crew_amount = fields.Monetary(string='Crew Amount', compute='_compute_crew_amount', store=True)
    crew_amount_signed = fields.Monetary(string='Crew Amount at the Signature', readonly=True, copy=False,
                                         help='Written when the act is signed; the amount of a signed act.')
    # F-22: the payment due before the installation (read only, from the invoices of the order)
    pay_ok = fields.Boolean(related='order_id.td_pay_ok', string='Paid before Installation')
    pay_missing = fields.Monetary(related='order_id.td_pay_missing', string='Missing before Installation')
    pay_control = fields.Selection(related='order_id.td_pay_control')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('td.mebli.install.act') or '/'
        # the act is opened when the crew starts at the customer: the payment control of the order (warn or block)
        tasks = self.env['project.task'].browse([vals['task_id'] for vals in vals_list if vals.get('task_id')])
        tasks.sale_order_id._td_check_payment(self.env._("Start the installation"))
        acts = super().create(vals_list)
        for act in acts.filtered(lambda a: not a.crew_line_ids and a.task_id.user_ids):
            # sudo: the crew of the visit is copied to the act; the crew lines are not created by the crew itself
            act.sudo().crew_line_ids = [(0, 0, {'user_id': user.id}) for user in act.task_id.user_ids]
        for act, vals in zip(acts, vals_list):  # an act created signed (import, data): the amount of the moment
            if vals.get('state') == 'signed' and 'crew_amount_signed' not in vals:
                # sudo: a signed act is read only for the crew; the system writes the amount of the moment
                act.sudo().crew_amount_signed = act._td_crew_amount_now()  # a signed act is read only for the crew
        return acts

    def write(self, vals):
        # AC-098 (SPEC text): a signed act is read only for everybody; the system (su) still writes its technical fields
        if not self.env.su and any(act.state == 'signed' for act in self):
            raise UserError(self.env._("A signed act cannot be changed"))
        self._td_fix_crew_amount(vals)
        return super().write(vals)

    @api.depends('defect_ids.resolved')
    def _compute_defects(self):
        for act in self:
            act.defect_open_count = len(act.defect_ids.filtered(lambda d: not d.resolved))

    def _td_crew_share(self):
        """VP-15: the share of the order (0..1) this act pays to the crew. «By the final act» (default): the final act
        pays all, the stage acts nothing. «By stages»: every act pays its share of the work, the final act the rest."""
        self.ensure_one()
        if (self.company_id or self.env.company).td_crew_base != 'stage':
            return 1.0 if self.kind == 'final' else 0.0
        if self.kind == 'stage':
            return max(0.0, min(100.0, self.stage_pct)) / 100.0
        # sudo: read only: the stage acts of the order, also the ones of other visits the crew does not see
        stages = self.sudo().search([('order_id', '=', self.order_id.id), ('kind', '=', 'stage'),
                                     ('state', '=', 'signed'), ('id', '!=', self._origin.id or 0)]) if self.order_id else []
        return max(0.0, 100.0 - sum(act.stage_pct for act in stages)) / 100.0

    def _td_crew_amount_now(self):
        self.ensure_one()
        return self.order_id.amount_untaxed * self.crew_pct / 100.0 * self._td_crew_share()

    def _td_crew_split(self, employees):
        """VP-14: {employee: share} of the crew amount — equally (default) or by the hours of the act."""
        self.ensure_one()
        if not employees:
            return {}
        if (self.company_id or self.env.company).td_crew_split == 'time':
            hours = {employee: sum(self.crew_line_ids.filtered(lambda line: line.user_id == employee.user_id).mapped('hours'))
                     for employee in employees}
            total = sum(hours.values())
            if total > 0:
                return {employee: value / total for employee, value in hours.items()}
        return {employee: 1.0 / len(employees) for employee in employees}

    @api.depends('kind', 'crew_pct', 'stage_pct', 'order_id.amount_untaxed', 'state', 'crew_amount_signed')
    def _compute_crew_amount(self):
        for act in self:
            act.crew_amount = act.crew_amount_signed if act.state == 'signed' else act._td_crew_amount_now()

    def _td_fix_crew_amount(self, vals):
        """The act becomes signed: the amount of the moment is written into the stored field (not read back by SQL)."""
        if vals.get('state') == 'signed' and 'crew_amount_signed' not in vals:
            for act in self.filtered(lambda a: a.state != 'signed'):
                super(TdMebliInstallAct, act).write({'crew_amount_signed': act._td_crew_amount_now()})

    @api.constrains('kind', 'order_id')
    def _check_one_final_act(self):
        for act in self.filtered(lambda a: a.kind == 'final' and a.order_id):
            # sudo: read only: one final act per order, also among the acts the user does not see
            if self.sudo().search_count([('kind', '=', 'final'), ('order_id', '=', act.order_id.id), ('id', '!=', act.id)]):
                raise ValidationError(self.env._("The order %s already has a final act: one final act per order, the "
                                                 "other visits get stage acts.", act.order_id.name))

    @api.constrains('photo_archive', 'photo_consent')
    def _check_photo_consent(self):
        if any(act.photo_archive and not act.photo_consent for act in self):
            raise ValidationError(self.env._("No consent of the customer to publish the photos"))

    def action_td_photo_archive(self):
        """AC-100: «To the photo archive» — also on a signed act (read only for the crew), only with the consent."""
        for act in self:
            act.check_access('read')
            if not act.photo_consent:
                raise UserError(self.env._("No consent of the customer to publish the photos"))
            # sudo: a signed act is read only; the photo consent is checked above, the system marks the archive
            act.sudo().photo_archive = True
            act.message_post(body=self.env._("The photos are in the photo archive."))
        return True

    def action_sign(self):
        for act in self:
            if act.state == 'signed':  # AC-098, SPEC text
                raise UserError(self.env._("A signed act cannot be changed"))
            if not act.signature:  # AC-098, SPEC text
                raise UserError(self.env._("There is no signature of the customer"))
            act.order_id._td_check_payment(self.env._("Sign the act"))
            act.write({'state': 'signed', 'signed_on': fields.Datetime.now()})
            if act.kind == 'final':
                act.task_id.state = '1_done'
        return True


class TdMebliInstallActCrew(models.Model):
    _name = 'td.mebli.install.act.crew'
    _description = 'Hours of an Installer at the Visit'
    _order = 'act_id, id'

    act_id = fields.Many2one('td.mebli.install.act', string='Act', required=True, ondelete='cascade', index=True)
    user_id = fields.Many2one('res.users', string='Installer', required=True)
    hours = fields.Float(string='Hours', digits=(16, 2))


class TdMebliInstallDefect(models.Model):
    _name = 'td.mebli.install.defect'
    _description = 'Defect in an Installation Act'
    _order = 'act_id, id'

    act_id = fields.Many2one('td.mebli.install.act', string='Act', required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Defect', required=True)
    photo = fields.Image(string='Photo', max_width=1024, max_height=1024)
    resolved = fields.Boolean(string='Resolved')
    company_id = fields.Many2one(related='act_id.company_id', store=True, string='Company')


class ProjectTask(models.Model):
    _inherit = 'project.task'

    td_act_ids = fields.One2many('td.mebli.install.act', 'task_id', string='Installation Acts')
    td_act_count = fields.Integer(string='Acts', compute='_compute_td_act_count')

    @api.depends('td_act_ids')
    def _compute_td_act_count(self):
        for task in self:
            task.td_act_count = len(task.td_act_ids)

    def action_td_view_acts(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('td_mebli_install.td_mebli_install_act_action')
        action['domain'] = [('task_id', '=', self.id)]
        action['context'] = {'default_task_id': self.id, 'create': True}
        if len(self.td_act_ids) == 1:
            action.update(view_mode='form', views=[(False, 'form')], res_id=self.td_act_ids.id)
        return action
