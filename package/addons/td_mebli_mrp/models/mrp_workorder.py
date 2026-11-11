from odoo import api, fields, models


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    td_capacity_hours = fields.Float(
        string='Available Hours per Week', default=80.0,
        help="Working hours the section can give to orders in a week (people x shift hours); the base of the load, %.")


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    td_expected_hours = fields.Float(
        string='Planned Hours', compute='_compute_td_load', store=True, digits=(16, 1))
    td_load_pct = fields.Float(
        string='Load, %', compute='_compute_td_load', store=True, digits=(16, 1), aggregator='sum',
        help="Share of the weekly capacity of the section taken by this operation; the sum over a section is its load.")
    td_load_stage = fields.Selection(
        [('work', 'In work'), ('queue', 'In queue'), ('chain', 'Waits for previous operation')],
        string='Shop Status', compute='_compute_td_load', store=True)
    td_load_zone = fields.Selection(
        [('within', 'Within capacity'), ('over', 'Over capacity')], string='Load Zone', compute='_compute_td_load_zone', store=True,
        help="Over capacity: the open work of the section needs more hours than the section has in a week.")

    @api.depends('workcenter_id.td_capacity_hours', 'workcenter_id.order_ids.duration_expected', 'workcenter_id.order_ids.state')
    def _compute_td_load_zone(self):
        for workorder in self:
            center = workorder.workcenter_id
            hours = sum(center.order_ids.filtered(lambda order: order.state not in ('done', 'cancel')).mapped('duration_expected')) / 60.0
            workorder.td_load_zone = 'over' if center.td_capacity_hours and hours > center.td_capacity_hours else 'within'

    @api.depends('duration_expected', 'state', 'workcenter_id.td_capacity_hours')
    def _compute_td_load(self):
        for workorder in self:
            hours = workorder.duration_expected / 60.0
            capacity = workorder.workcenter_id.td_capacity_hours
            workorder.td_expected_hours = hours
            workorder.td_load_pct = hours / capacity * 100.0 if capacity else 0.0
            workorder.td_load_stage = {'progress': 'work', 'pending': 'chain'}.get(workorder.state, 'queue')
