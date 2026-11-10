from odoo.tests import Form, tagged

from .common import TdMebliCuttingCommon


@tagged('post_install', '-at_install')
class TestCuttingDone(TdMebliCuttingCommon):

    def _job(self):
        production = self._make_production()
        job = self.env['td.mebli.cutting.job'].create({'production_ids': [(6, 0, production.ids)]})
        return production, job

    def test_flow_states_and_file(self):
        production, job = self._job()
        self.assertEqual(job.state, 'draft')
        self.assertTrue(job.name.startswith('CUT/'))
        job.action_send()
        self.assertEqual(job.state, 'sent')
        self.assertIn('draft-format', job.export_attachment_id.name)
        self.assertEqual(production.td_cutting_job_ids, job)
        job.action_simulate()
        self.assertEqual(job.state, 'result')
        self.assertEqual(job.result_source, 'simulated')
        self.assertTrue(job.sheet_ids)
        self.assertTrue(0 <= job.waste_pct < 100)

    def test_reserve_and_offcuts(self):
        production, job = self._job()
        job.action_send()
        job.action_simulate()
        offcut_areas = sum(job.sheet_ids.offcut_ids.mapped('area_m2'))
        self.assertGreater(offcut_areas, 0)
        job.action_done()
        self.assertEqual(job.state, 'done')
        # sheets are reserved by lot
        board_move = production.move_raw_ids.filtered(lambda m: m.product_id == self.board_a)
        reserved_lots = board_move.move_line_ids.lot_id
        used_lots = job.sheet_ids.filtered(lambda s: s.product_id == self.board_a).lot_id
        self.assertEqual(reserved_lots, used_lots)
        # offcut lots with sizes
        offcut_lots = self.env['stock.lot'].search([('td_cutting_job_id', '=', job.id)])
        self.assertEqual(len(offcut_lots), len(job.sheet_ids.offcut_ids))
        for lot in offcut_lots:
            self.assertTrue(lot.td_is_offcut)
            self.assertGreaterEqual(lot.td_length_mm, job.min_offcut_mm)
            self.assertTrue(lot.name.startswith('OFF-'))
        # offcuts become stock once the manufacturing order is done
        self._finish(production)
        for lot in offcut_lots:
            quants = self.env['stock.quant'].search([
                ('lot_id', '=', lot.id), ('location_id', 'child_of', self.stock_location.id)])
            self.assertAlmostEqual(sum(quants.mapped('quantity')), lot.td_area_m2, delta=0.0011)

    def _finish(self, production):
        for workorder in production.workorder_ids:
            workorder.button_start()
            workorder.button_finish()
        form = Form(production)
        form.qty_producing = production.product_qty
        production = form.save()
        production.with_context(skip_consumption=True, skip_backorder=True).button_mark_done()
        self.assertEqual(production.state, 'done')

    def test_offcut_valuation(self):
        production, job = self._job()
        job.action_send()
        job.action_simulate()
        job.action_done()
        self._finish(production)
        offcut_lots = self.env['stock.lot'].search([('td_cutting_job_id', '=', job.id), ('product_id', '=', self.board_a.id)])
        self.assertTrue(offcut_lots)
        moves = production.move_finished_ids.filtered(lambda m: m.product_id == self.board_a and m.state == 'done')
        self.assertEqual(len(moves), len(offcut_lots))
        for move in moves:
            lot = move.move_line_ids.lot_id
            expected = lot.td_area_m2 * self.board_a.standard_price
            self.assertGreater(move.value, 0.0)
            self.assertAlmostEqual(move.value, expected, delta=expected * 0.5)
