from odoo import api, fields, models
from odoo.exceptions import AccessError


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    td_quality_point = fields.Char(
        string='Quality Step',
        help="What the worker checks and photographs before «Done», e.g. «edge without chips, photo of the end».")


class MrpWorkcenterProductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    td_employee_id = fields.Many2one(
        'hr.employee', string='Worker', index='btree_not_null', readonly=True,
        help="Who confirmed the step with the PIN on the shop floor tablet (the time itself is the standard time line).")

    def _td_check_employee_write(self, vals_list):
        """The worker of a time line is set by the tablet after the PIN (sudo) or by the shop manager, not by any
        manufacturing user through the API."""
        if self.env.su or self.env.user.has_group('mrp.group_mrp_manager'):
            return
        if any(vals.get('td_employee_id') for vals in vals_list):
            raise AccessError(self.env._("Only the shop floor tablet (with the PIN) or the shop manager sets the worker "
                                         "of a time line."))

    @api.model_create_multi
    def create(self, vals_list):
        self._td_check_employee_write(vals_list)
        return super().create(vals_list)

    def copy(self, default=None):
        """The standard split of an overrun timer (mrp.workcenter.productivity._close: the time over the plan becomes a
        copy with the loss «Reduced Speed») keeps the worker of the original line. The copy carries the same worker, it
        does not set a new one, so it is allowed for every user; a worker given explicitly in `default` is checked."""
        default = dict(default or {})
        if 'td_employee_id' in default or self.env.su or self.env.user.has_group('mrp.group_mrp_manager'):
            return super().copy(default)
        default['td_employee_id'] = False
        copies = super().copy(default)
        for line, new in zip(self, copies):
            if line.td_employee_id:
                new.sudo().write({'td_employee_id': line.td_employee_id.id})
        return copies

    def write(self, vals):
        if 'td_employee_id' in vals:
            self._td_check_employee_write([dict(vals, td_employee_id=vals['td_employee_id'] or True)])
        return super().write(vals)


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    td_quality_point = fields.Char(related='operation_id.td_quality_point', string='Quality Step')
    td_quality_ids = fields.One2many('td.mebli.quality.check', 'workorder_id', string='Quality Checks')
    td_quality_state = fields.Selection(
        [('none', 'No Step'), ('todo', 'To Check'), ('pass', 'Passed'), ('fail', 'Failed')],
        string='Quality', compute='_compute_td_quality_state')
    td_worker_names = fields.Char(string='Workers', compute='_compute_td_worker_names')
    td_pause_reason = fields.Char(string='Pause Reason', compute='_compute_td_worker_names')

    @api.depends('td_quality_point', 'td_quality_ids.result', 'td_quality_ids.kind')
    def _compute_td_quality_state(self):
        for workorder in self:
            # a scrap (AC-073) is a non-conformity of a part, not the quality step of the operation
            last = workorder.td_quality_ids.filtered(lambda check: check.kind == 'check').sorted('id')[-1:]
            if not workorder.td_quality_point:
                workorder.td_quality_state = 'none'
            else:
                workorder.td_quality_state = last.result or 'todo'

    @api.depends('time_ids.td_employee_id', 'time_ids.date_end', 'time_ids.loss_type')
    def _compute_td_worker_names(self):
        for workorder in self:
            # who works on it now: only the open time lines (a worker who paused or finished is not «in work»)
            running = workorder.time_ids.filtered(lambda t: not t.date_end and t.loss_type == 'productive')
            workorder.td_worker_names = ', '.join(running.td_employee_id.mapped('name'))
            pause = workorder.time_ids.filtered(lambda t: not t.date_end and t.loss_type != 'productive')[:1]
            workorder.td_pause_reason = pause.loss_id.name or ''

    def action_td_kiosk(self):
        """Opens the PIN dialog of the tablet for the button pressed (context td_action)."""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('td_mebli_shop.td_mebli_kiosk_action')
        action['context'] = {'default_workorder_id': self.id,
                             'default_action': self.env.context.get('td_action', 'start')}
        return action


class TdMebliQualityCheck(models.Model):
    _name = 'td.mebli.quality.check'
    _description = 'Quality Check of a Work Order'
    _order = 'id desc'

    workorder_id = fields.Many2one('mrp.workorder', string='Work Order', required=True, ondelete='cascade', index=True)
    production_id = fields.Many2one(related='workorder_id.production_id', store=True, string='Manufacturing Order')
    workcenter_id = fields.Many2one(related='workorder_id.workcenter_id', store=True, string='Work Center')
    name = fields.Char(string='Quality Step', required=True)
    result = fields.Selection([('pass', 'Passed'), ('fail', 'Failed')], string='Result', required=True)
    photo = fields.Image(string='Photo', max_width=1024, max_height=1024)
    note = fields.Char(string='Note')
    # created only by the tablet after the PIN (sudo): the manufacturing users have no create right (ir.model.access)
    employee_id = fields.Many2one('hr.employee', string='Worker', readonly=True)
    # AC-073 / AC-121: the journal of non-conformities — a failed quality step or a scrap at the workplace with its
    # reason (note) and the manufacturing order of the repeat part; the dashboard counts the failed lines
    kind = fields.Selection([('check', 'Quality Step'), ('scrap', 'Scrap')], string='Kind', required=True,
                            default='check', index=True)
    part_id = fields.Many2one('td.mebli.part', string='Part', readonly=True, ondelete='set null')
    repeat_production_id = fields.Many2one('mrp.production', string='Repeat Part Order', readonly=True)
    company_id = fields.Many2one(related='workorder_id.company_id', store=True, string='Company')
