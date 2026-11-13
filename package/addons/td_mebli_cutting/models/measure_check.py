from odoo import fields, models


class TdMebliCuttingJob(models.Model):
    """Position 28: before the parts go to cutting (own workshop or the distributor) the design of the orders is checked
    against their measurement sheets by rules (td_mebli_measure); a problem asks for a confirmation, it does not block."""
    _inherit = 'td.mebli.cutting.job'

    td_measure_problems = fields.Text(string='Design against the Measurement', compute='_compute_td_measure_problems')
    td_measure_missing = fields.Boolean(string='No Measurement', compute='_compute_td_measure_missing')

    def _compute_td_measure_missing(self):
        """AC-056: an order of the job has no measurement sheet — the check against the measurement is skipped."""
        for job in self:
            orders = job.production_ids._td_sale_orders()
            job.td_measure_missing = not orders or any(not order.sudo().td_measure_ids for order in orders)

    def _td_warn_no_measure(self):
        if self.env.context.get('td_measure_ack'):
            return  # the check against the measurement found problems: there is a measurement
        for job in self.filtered('td_measure_missing'):
            job.message_post(body=self.env._("The measurement is not filled in — the check is skipped"))

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
        gate = self._td_measure_gate('action_send')
        if gate:
            return gate
        if not self.env.context.get('td_measure_warned'):
            self._td_warn_no_measure()  # AC-056: a warning, the sending is not blocked
        return super().action_send()

    def action_send_distributor(self):
        gate = self._td_measure_gate('action_send_distributor')
        if gate:
            return gate
        self._td_warn_no_measure()
        # the distributor sending calls action_send itself: one warning is enough
        return super(TdMebliCuttingJob, self.with_context(td_measure_warned=True)).action_send_distributor()


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
