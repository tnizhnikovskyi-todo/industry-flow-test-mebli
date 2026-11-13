from datetime import timedelta

from odoo import fields, models
from odoo.exceptions import UserError

VISIT_HOURS = 4  # default length of an installation visit in Planning until the norm of the visit is set (assumption)


class PlanningSlot(models.Model):
    _inherit = 'planning.slot'

    td_task_id = fields.Many2one('project.task', string='Installation Visit', index='btree_not_null', ondelete='set null')


class ProjectTask(models.Model):
    _inherit = 'project.task'

    td_slot_ids = fields.One2many('planning.slot', 'td_task_id', string='Planning Shifts')

    def action_td_plan_crew(self):
        """AC-128: the crew of the visit (assignees with an employee) gets Planning shifts at the date of the visit."""
        Slot = self.env['planning.slot']
        for task in self:
            if not task.date_deadline:
                raise UserError(self.env._("Set the date of the visit first."))
            task.td_slot_ids.unlink()
            employees = task.user_ids.employee_id.filtered(lambda e: e.company_id == task.company_id or not e.company_id)
            for employee in employees:
                Slot.create({'resource_id': employee.resource_id.id, 'start_datetime': task.date_deadline,
                             'end_datetime': task.date_deadline + timedelta(hours=VISIT_HOURS),
                             'name': task.name, 'td_task_id': task.id, 'company_id': task.company_id.id})
        return True
