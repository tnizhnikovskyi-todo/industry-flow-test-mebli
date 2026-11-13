from odoo import fields, models


class TdMebliCuttingJob(models.Model):
    """Position 28: before the parts go to cutting (own workshop or the distributor) the design of the orders is checked
    against their measurement sheets by rules (td_mebli_measure); a problem asks for a confirmation, it does not block."""
    _inherit = 'td.mebli.cutting.job'

    td_measure_problems = fields.Text(string='Design against the Measurement', compute='_compute_td_measure_problems')

    def _compute_td_measure_problems(self):
        for job in self:
            problems = []
            for production in job.production_ids:
                problems += (production.td_measure_problems or '').splitlines()
            job.td_measure_problems = '\n'.join(dict.fromkeys(p for p in problems if p)) or False

    def _td_measure_gate(self, method):
        if self.env.context.get('td_measure_ack'):
            return None
        jobs = self.filtered('td_measure_problems')
        if not jobs:
            return None
        wizard = self.env['td.mebli.measure.warning'].create({
            'job_ids': [(6, 0, self.ids)], 'method': method,
            'problems': '\n'.join(jobs.mapped('td_measure_problems'))})
        return {'type': 'ir.actions.act_window', 'res_model': wizard._name, 'res_id': wizard.id, 'view_mode': 'form',
                'target': 'new', 'name': self.env._("Check before Cutting")}

    def action_send(self):
        return self._td_measure_gate('action_send') or super().action_send()

    def action_send_distributor(self):
        return self._td_measure_gate('action_send_distributor') or super().action_send_distributor()


class TdMebliMeasureWarning(models.TransientModel):
    _name = 'td.mebli.measure.warning'
    _description = 'Check of the Design against the Measurement before Cutting'

    job_ids = fields.Many2many('td.mebli.cutting.job', string='Cutting Jobs')
    method = fields.Selection([('action_send', 'Send to cutting'), ('action_send_distributor', 'Send to the distributor')],
                              required=True)
    problems = fields.Text(string='What does not Fit', readonly=True)

    def action_confirm(self):
        self.ensure_one()
        jobs = self.job_ids.with_context(td_measure_ack=True)
        for job in jobs:
            job.message_post(body=self.env._("Sent to cutting despite the check against the measurement: %s",
                                             self.problems))
        getattr(jobs, self.method)()
        return {'type': 'ir.actions.act_window_close'}
