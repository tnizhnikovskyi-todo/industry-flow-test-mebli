from odoo import api, fields, models

INSTALL_STAGES = ('stage_install_to_plan', 'stage_install_planned', 'stage_install_installed',
                  'stage_install_act_signed', 'stage_install_cancelled')


class ProjectProject(models.Model):
    _inherit = 'project.project'

    # A-17 №16: the project of the installation visits gets the stages of the visits (config package A-12 sets the flag)
    td_install_project = fields.Boolean(
        string='Installation Project',
        help="The project of the installation visits: its tasks get the stages To Plan, Planned, Installed, Act Signed, "
             "Cancelled, and the date of the visit from the delivery date of the order.")

    def _td_link_install_stages(self):
        stages = self.env['project.task.type']
        for xmlid in INSTALL_STAGES:
            stages |= self.env.ref(f'td_mebli_install.{xmlid}', raise_if_not_found=False) or stages.browse()
        for project in self.filtered('td_install_project'):
            # sudo: the stages are shared records (project.task.type), linked by the system when the flag is set
            missing = stages.sudo().filtered_domain([('project_ids', 'not in', project.ids)])
            if missing:
                project.sudo().type_ids = [(4, stage.id) for stage in missing]

    @api.model_create_multi
    def create(self, vals_list):
        projects = super().create(vals_list)
        projects._td_link_install_stages()
        return projects

    def write(self, vals):
        result = super().write(vals)
        if vals.get('td_install_project'):
            self._td_link_install_stages()
        return result


class ProjectTask(models.Model):
    _inherit = 'project.task'

    def _td_planned_stage_move(self):
        """A-17 №16: a visit «To Plan» with a date of the visit goes to «Planned» (by the system, once)."""
        to_plan = self.env.ref('td_mebli_install.stage_install_to_plan', raise_if_not_found=False)
        planned = self.env.ref('td_mebli_install.stage_install_planned', raise_if_not_found=False)
        if not to_plan or not planned:
            return
        tasks = self.filtered(lambda t: t.date_deadline and t.stage_id == to_plan and planned in t.project_id.type_ids)
        if tasks:
            # sudo: the stage follows the date — also when the salesperson plans the date (D-19: date and crew only)
            tasks.sudo().with_context(td_install_stage_auto=True).write({'stage_id': planned.id})

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        tasks._td_planned_stage_move()
        return tasks

    def write(self, vals):
        result = super().write(vals)
        if 'date_deadline' in vals and not self.env.context.get('td_install_stage_auto'):
            self._td_planned_stage_move()
        return result


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _timesheet_create_task_prepare_values(self, project):
        """A-17 №16: the visit task gets the date of the visit from the delivery date of the order (commitment_date):
        the «Installation Calendar» and «My Day» of the foreman read the deadline of the task."""
        values = super()._timesheet_create_task_prepare_values(project)
        if self.order_id.commitment_date and not values.get('date_deadline'):
            values['date_deadline'] = self.order_id.commitment_date
        return values


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def write(self, vals):
        """A-17 №16: a new delivery date moves the visits that still had the old one (or none); a visit planned by hand
        to another date keeps it."""
        if 'commitment_date' not in vals:
            return super().write(vals)
        old = {order.id: order.commitment_date for order in self}
        result = super().write(vals)
        for order in self:
            before = old[order.id]
            if order.commitment_date == before or not order.commitment_date:
                continue
            # sudo: the visits of the order (project.task) — the salesperson may have no Project rights
            tasks = order.sudo().td_task_ids.filtered_domain([
                ('state', 'not in', ('1_done', '1_canceled')), ('td_visit_kind', '!=', 'service'),
                '|', ('date_deadline', '=', False), ('date_deadline', '=', before)])
            if tasks:
                tasks.write({'date_deadline': order.commitment_date})
        return result


class TdMebliInstallAct(models.Model):
    _inherit = 'td.mebli.install.act'

    def write(self, vals):
        result = super().write(vals)
        if vals.get('state') == 'signed':
            stage = self.env.ref('td_mebli_install.stage_install_act_signed', raise_if_not_found=False)
            # sudo: the stage of the visit follows its signed final act (the crew may have no right on the stage)
            tasks = self.filtered(lambda a: a.kind == 'final').sudo().task_id.filtered(
                lambda t: stage and stage in t.project_id.type_ids and t.stage_id != stage)
            if tasks:
                tasks.with_context(td_install_stage_auto=True).write({'stage_id': stage.id})
        return result
