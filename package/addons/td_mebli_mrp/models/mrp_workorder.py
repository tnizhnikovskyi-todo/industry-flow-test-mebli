from odoo import api, fields, models


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    # the hours come from the standard working calendar of the section, nothing is entered here
    td_capacity_hours = fields.Float(
        string='Available Hours per Week', compute='_compute_td_capacity_hours', digits=(16, 1),
        help="Read only: hours per week of the working calendar of the section times the number of pieces it makes in "
             "parallel (the product capacity without a product). The time efficiency is not applied here: it is already "
             "in the expected duration of the operations.")

    @api.depends('resource_calendar_id.hours_per_week', 'capacity_ids.capacity', 'capacity_ids.product_id')
    def _compute_td_capacity_hours(self):
        for center in self:
            general = center.capacity_ids.filtered(lambda capacity: not capacity.product_id)[:1]
            parallel = general.capacity if general.capacity > 0 else 1.0
            center.td_capacity_hours = center.resource_calendar_id.hours_per_week * parallel


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    td_expected_hours = fields.Float(
        string='Planned Hours', compute='_compute_td_load', store=True, digits=(16, 1))
    td_load_pct = fields.Float(
        string='Load, %', compute='_compute_td_load', store=True, digits=(16, 1), aggregator='sum',
        help="Share of the weekly capacity of the section taken by this operation; summed over a section and the week of "
             "the planned start it is the load of that week.")
    td_load_stage = fields.Selection(
        [('work', 'In work'), ('queue', 'In queue'), ('chain', 'Waits for previous operation')],
        string='Shop Status', compute='_compute_td_load', store=True)
    td_load_zone = fields.Selection(
        [('within', 'Within capacity'), ('over', 'Over capacity')], string='Load Zone', compute='_compute_td_load_zone', store=True,
        help="Over capacity: the open work of the section (standard work center load) needs more hours than the section "
             "has in a week.")

    @api.depends('workcenter_id.workcenter_load', 'workcenter_id.resource_calendar_id.hours_per_week',
                 'workcenter_id.capacity_ids.capacity')
    def _compute_td_load_zone(self):
        for workorder in self:
            center = workorder.workcenter_id
            hours = center.workcenter_load / 60.0  # standard: minutes of the blocked, ready and running work orders
            capacity = center.td_capacity_hours
            workorder.td_load_zone = 'over' if capacity and hours > capacity else 'within'

    @api.depends('duration_expected', 'state', 'workcenter_id.resource_calendar_id.hours_per_week',
                 'workcenter_id.capacity_ids.capacity')
    def _compute_td_load(self):
        for workorder in self:
            hours = workorder.duration_expected / 60.0
            capacity = workorder.workcenter_id.td_capacity_hours
            workorder.td_expected_hours = hours
            workorder.td_load_pct = hours / capacity * 100.0 if capacity else 0.0
            workorder.td_load_stage = {'progress': 'work', 'blocked': 'chain'}.get(workorder.state, 'queue')

    # the parts of the manufacturing order of this operation, for the tablet of the shop (read only, not stored)
    td_part_ids = fields.One2many(related='production_id.bom_id.td_part_ids', string='Parts', readonly=True)
    td_part_count = fields.Integer(related='production_id.td_part_count', string='Part Count')

    def action_td_parts(self):
        """Parts of the manufacturing order in a dialog of the tablet (read only)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._("Parts: %s", self.production_id.display_name),
            'res_model': 'mrp.workorder',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(self.env.ref('td_mebli_mrp.mrp_workorder_td_parts_form').id, 'form')],
            'target': 'new',
        }
