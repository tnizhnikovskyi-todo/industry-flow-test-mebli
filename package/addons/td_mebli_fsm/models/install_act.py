from odoo import fields, models


class TdMebliInstallAct(models.Model):
    _inherit = 'td.mebli.install.act'

    # AC-128: on EE the visit is a Field Service task (project.task with is_fsm); the act and the crew percent stay on it
    td_is_fsm = fields.Boolean(related='task_id.is_fsm', string='Field Service Task')

