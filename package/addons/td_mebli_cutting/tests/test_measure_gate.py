from odoo.tests import tagged

from .common import TdMebliCuttingCommon


def _fridge(records):
    for production in records:
        production.td_measure_problems = 'Fridge: deeper by 30 mm'


@tagged('post_install', '-at_install')
class TestMeasureGate(TdMebliCuttingCommon):
    """F-62: a problem of the measurement asks for a confirmation before cutting, it does not block."""

    def test_no_problem_no_question(self):
        job = self.env['td.mebli.cutting.job'].create({'production_ids': [(6, 0, self._make_production().ids)]})
        job.action_send()
        self.assertEqual(job.state, 'sent')

    def test_warning_then_send_anyway(self):
        production = self._make_production()
        job = self.env['td.mebli.cutting.job'].create({'production_ids': [(6, 0, production.ids)]})
        # the rules of td_mebli_measure are tested there; here only the gate: a problem is given
        self.patch(type(production), '_compute_td_measure_problems', _fridge)
        production.invalidate_recordset()
        job.invalidate_recordset()
        action = job.action_send()
        self.assertEqual(action['res_model'], 'td.mebli.measure.warning')
        self.assertEqual(job.state, 'draft')
        warning = self.env['td.mebli.measure.warning'].browse(action['res_id'])
        self.assertIn('30 mm', warning.problems)
        warning.action_confirm()
        self.assertEqual(job.state, 'sent')
        self.assertIn('30 mm', job.message_ids[:1].body)
