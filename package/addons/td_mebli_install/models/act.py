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
    crew_user_ids = fields.Many2many(related='task_id.user_ids', string='Crew')
    kind = fields.Selection([('stage', 'Stage Act'), ('final', 'Final Act')], string='Kind', required=True,
                            default='final', tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('signed', 'Signed')], string='Status', default='draft',
                             tracking=True, copy=False)
    signature = fields.Image(string='Signature of the Customer', copy=False, max_width=1024, max_height=512)
    signed_by = fields.Char(string='Signed by', copy=False)
    signed_on = fields.Datetime(string='Signed on', readonly=True, copy=False)
    checklist = fields.Text(string='Checklist', default=lambda self: self.env._(
        "Fronts adjusted\nGaps are even\nAppliances connected by the customer's technician\nWorkplace cleaned"))
    defect_ids = fields.One2many('td.mebli.install.defect', 'act_id', string='Defects')
    defect_open_count = fields.Integer(string='Open Defects', compute='_compute_defects')
    photo_ids = fields.Many2many('ir.attachment', string='Photos')
    photo_archive = fields.Boolean(string='In the Photo Archive',
                                   help='The photos may be used for advertising (the consent is in the act).')
    crew_pct = fields.Float(string='Crew, %', digits=(5, 2), default=5.0,
                            help='Share of the order amount (without taxes) paid to the crew for the installation.')
    currency_id = fields.Many2one(related='order_id.currency_id')
    # fixed at the signature: a later change of the order does not change the amount of a signed act
    crew_amount = fields.Monetary(string='Crew Amount', compute='_compute_crew_amount', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('td.mebli.install.act') or '/'
        return super().create(vals_list)

    @api.depends('defect_ids.resolved')
    def _compute_defects(self):
        for act in self:
            act.defect_open_count = len(act.defect_ids.filtered(lambda d: not d.resolved))

    @api.depends('kind', 'crew_pct', 'order_id.amount_untaxed')
    def _compute_crew_amount(self):
        # a signed act keeps the amount it was signed with (read from the database: the act may be created signed)
        saved = {}
        ids = [act.id for act in self if isinstance(act.id, int)]
        if ids:
            self.env.cr.execute("SELECT id, crew_amount FROM td_mebli_install_act "
                                "WHERE id IN %s AND state = 'signed' AND crew_amount IS NOT NULL", [tuple(ids)])
            saved = dict(self.env.cr.fetchall())
        for act in self:
            if act.id in saved:
                act.crew_amount = saved[act.id]
                continue
            act.crew_amount = act.order_id.amount_untaxed * act.crew_pct / 100.0 if act.kind == 'final' else 0.0

    @api.constrains('kind', 'order_id')
    def _check_one_final_act(self):
        for act in self.filtered(lambda a: a.kind == 'final' and a.order_id):
            if self.sudo().search_count([('kind', '=', 'final'), ('order_id', '=', act.order_id.id), ('id', '!=', act.id)]):
                raise ValidationError(self.env._("The order %s already has a final act: one final act per order, the "
                                                 "other visits get stage acts.", act.order_id.name))

    def action_sign(self):
        for act in self:
            if not act.signature:
                raise UserError(self.env._("The customer signs the act with a finger on the screen first."))
            act.write({'state': 'signed', 'signed_on': fields.Datetime.now()})
            if act.kind == 'final':
                act.task_id.state = '1_done'
        return True


class TdMebliInstallDefect(models.Model):
    _name = 'td.mebli.install.defect'
    _description = 'Defect in an Installation Act'
    _order = 'act_id, id'

    act_id = fields.Many2one('td.mebli.install.act', string='Act', required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Defect', required=True)
    photo = fields.Image(string='Photo', max_width=1024, max_height=1024)
    resolved = fields.Boolean(string='Resolved')


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
