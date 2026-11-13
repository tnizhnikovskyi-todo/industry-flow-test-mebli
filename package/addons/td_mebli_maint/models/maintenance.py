from odoo import api, fields, models
from odoo.exceptions import UserError


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    td_workcenter_id = fields.Many2one(
        'mrp.workcenter', string='Work Center', index='btree_not_null', check_company=True,
        help="The section of the shop floor where the machine works: its breakdowns stop this work center.")


class MaintenanceRequest(models.Model):
    """A breakdown of a machine is a standard corrective request; while it is open the work center is down. The downtime
    is the standard time log of the work center (mrp.workcenter.productivity) with the standard loss reason «Equipment
    Failure» (mrp.block_reason1): the efficiency reports of Manufacturing and the morning briefing read it."""
    _inherit = 'maintenance.request'

    td_workcenter_id = fields.Many2one(related='equipment_id.td_workcenter_id', string='Work Center')
    td_downtime_id = fields.Many2one('mrp.workcenter.productivity', string='Downtime', readonly=True, copy=False,
                                     index='btree_not_null')
    td_downtime_open = fields.Boolean(string='Section Down', compute='_compute_td_downtime')
    td_downtime_hours = fields.Float(string='Downtime, h', compute='_compute_td_downtime', digits=(16, 1))

    @api.depends('td_downtime_id.date_end', 'td_downtime_id.duration')
    def _compute_td_downtime(self):
        for request in self:
            # sudo: read only: the downtime line of manufacturing (the maintenance user has no manufacturing rights)
            row = request.sudo().td_downtime_id
            request.td_downtime_open = bool(row) and not row.date_end
            request.td_downtime_hours = (row.duration or 0.0) / 60.0

    def action_td_start_downtime(self):
        for request in self:
            if not request.td_workcenter_id:
                raise UserError(self.env._("The machine has no work center: set it on the equipment."))
            if request.td_downtime_id:
                continue
            # sudo: the maintenance team writes the downtime of the section without rights in Manufacturing
            request.td_downtime_id = self.env['mrp.workcenter.productivity'].sudo().create({
                'workcenter_id': request.td_workcenter_id.id, 'loss_id': self.env.ref('mrp.block_reason1').id,
                'description': request.name, 'date_start': fields.Datetime.now(),
            })
        return True

    def action_td_stop_downtime(self):
        # sudo: the maintenance user closes the downtime of his request, a line of manufacturing
        self.filtered('td_downtime_open').td_downtime_id.sudo().write({'date_end': fields.Datetime.now()})
        return True

    def write(self, vals):
        result = super().write(vals)
        if vals.get('stage_id') and self.env['maintenance.stage'].browse(vals['stage_id']).done:
            self.action_td_stop_downtime()
        return result


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    td_equipment_count = fields.Integer(string='Machines', compute='_compute_td_equipment')
    td_request_open_count = fields.Integer(string='Open Requests', compute='_compute_td_equipment')

    def _compute_td_equipment(self):
        Equipment = self.env['maintenance.equipment']
        Request = self.env['maintenance.request']
        for center in self:
            center.td_equipment_count = Equipment.search_count([('td_workcenter_id', '=', center.id)]) if center.id else 0
            center.td_request_open_count = Request.search_count([
                ('equipment_id.td_workcenter_id', '=', center.id), ('stage_id.done', '=', False)]) if center.id else 0

    def action_td_view_requests(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('maintenance.hr_equipment_request_action')
        action['domain'] = [('equipment_id.td_workcenter_id', '=', self.id)]
        return action
