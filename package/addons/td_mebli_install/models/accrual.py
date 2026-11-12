from odoo import api, fields, models


class TdMebliAccrual(models.Model):
    _name = 'td.mebli.accrual'
    _description = 'Accrual to a Worker or a Crew'
    _order = 'date desc, id desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, index=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    kind = fields.Selection([('piece', 'Piecework'), ('crew', 'Crew Percent'), ('bonus', 'Bonus'), ('penalty', 'Penalty')],
                            string='Kind', required=True)
    hours = fields.Float(string='Hours', digits=(16, 2))
    amount = fields.Monetary(string='Amount', required=True)
    reason = fields.Char(string='Reason')
    productivity_id = fields.Many2one('mrp.workcenter.productivity', string='Time Line', ondelete='set null', readonly=True)
    workcenter_id = fields.Many2one(related='productivity_id.workcenter_id', store=True, string='Work Center')
    act_id = fields.Many2one('td.mebli.install.act', string='Act', ondelete='set null', readonly=True)
    order_ref = fields.Char(string='Order', compute='_compute_order_ref', store=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one(related='company_id.currency_id')
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed')], string='Status', default='draft')

    _reason_required = models.Constraint(
        "CHECK(kind NOT IN ('bonus', 'penalty') OR reason IS NOT NULL)",
        'A bonus or a penalty needs a reason.')

    @api.depends('productivity_id.production_id.origin', 'act_id.order_id.name')
    def _compute_order_ref(self):
        for accrual in self:
            accrual.order_ref = accrual.act_id.order_id.name or accrual.productivity_id.production_id.origin or ''

    @api.model
    def action_td_accrue(self):
        """Piecework from the finished time lines of the tablet and the crew percent from the signed final acts that have
        no accrual yet; bonuses and penalties are entered by hand."""
        vals = []
        lines = self.env['mrp.workcenter.productivity'].search([
            ('td_employee_id', '!=', False), ('date_end', '!=', False), ('loss_type', '=', 'productive')])
        done = set(self.search([('productivity_id', 'in', lines.ids)]).productivity_id.ids)
        for line in lines.filtered(lambda line: line.id not in done):
            hours = line.duration / 60.0
            vals.append({'employee_id': line.td_employee_id.id, 'date': fields.Date.context_today(self, line.date_end),
                         'kind': 'piece', 'hours': hours, 'amount': round(hours * line.td_employee_id.hourly_cost, 2),
                         'productivity_id': line.id, 'reason': line.workorder_id.name})
        acts = self.env['td.mebli.install.act'].search([('state', '=', 'signed'), ('kind', '=', 'final')])
        accrued = set(self.search([('act_id', 'in', acts.ids)]).act_id.ids)
        for act in acts.filtered(lambda a: a.id not in accrued):
            crew = act.crew_user_ids.employee_ids
            for employee in crew:
                vals.append({'employee_id': employee.id, 'date': fields.Date.context_today(self, act.signed_on),
                             'kind': 'crew', 'amount': round(act.crew_amount / len(crew), 2), 'act_id': act.id,
                             'reason': act.name})
        self.create(vals)
        return {'type': 'ir.actions.client', 'tag': 'soft_reload'}
