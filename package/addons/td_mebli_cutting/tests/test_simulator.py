from odoo.tests import tagged

from odoo.addons.td_mebli_cutting.models import optimizer

from .common import TdMebliCuttingCommon


def _piece(index, length, width, part_id=1, production_id=1):
    return {'part_id': part_id, 'production_id': production_id, 'index': index, 'length': length, 'width': width}


@tagged('post_install', '-at_install')
class TestSimulator(TdMebliCuttingCommon):

    def test_deterministic(self):
        pieces = [_piece(i, 700 + 10 * i, 500) for i in range(5)] + [_piece(9, 1200, 400)]
        sources = [{'lot_id': 1, 'length': 2800, 'width': 2070, 'is_offcut': False}]
        first = optimizer.pack(list(pieces), sources, None, kerf=4, trim=10, min_offcut=300)
        second = optimizer.pack(list(reversed(pieces)), sources, None, kerf=4, trim=10, min_offcut=300)
        self.assertEqual(first, second)
        sheet = first[0]
        self.assertEqual(len(sheet['placements']), 6)
        # trim and kerf: the first piece of every shelf starts at the trim, the next one after the kerf
        shelves = {}
        for p in sorted(sheet['placements'], key=lambda p: (p['y'], p['x'])):
            shelves.setdefault(p['y'], []).append(p)
        self.assertEqual(min(shelves), 10)
        for row in shelves.values():
            self.assertEqual(row[0]['x'], 10)
            for left, right in zip(row, row[1:]):
                self.assertEqual(right['x'], left['x'] + left['length'] + 4)
        # no overlap and inside the sheet
        for p in sheet['placements']:
            self.assertGreaterEqual(p['x'], 10)
            self.assertLessEqual(p['x'] + p['length'], 2800 - 10)
            self.assertLessEqual(p['y'] + p['width'], 2070 - 10)
        for index, a in enumerate(sheet['placements']):
            for b in sheet['placements'][index + 1:]:
                overlap = (a['x'] < b['x'] + b['length'] and b['x'] < a['x'] + a['length']
                           and a['y'] < b['y'] + b['width'] and b['y'] < a['y'] + a['width'])
                self.assertFalse(overlap)

    def test_offcut_reuse_first(self):
        offcut = {'lot_id': 7, 'length': 1200, 'width': 700, 'is_offcut': True}
        sheet = {'lot_id': 8, 'length': 2800, 'width': 2070, 'is_offcut': False}
        result = optimizer.pack([_piece(0, 500, 400)], [offcut, sheet], None)
        self.assertEqual([s['lot_id'] for s in result], [7])
        # a part that does not fit the offcut goes to the whole sheet and the offcut stays untouched
        result = optimizer.pack([_piece(0, 1500, 400)], [offcut, sheet], None)
        self.assertEqual([s['lot_id'] for s in result], [8])

    def test_part_too_large(self):
        with self.assertRaises(optimizer.PieceTooLarge):
            optimizer.pack([_piece(0, 5000, 400)], [], {'length': 2800, 'width': 2070})

    def test_job_uses_offcut_lot_first(self):
        offcut_lots = self._add_lots(self.board_a, 1, length=1200, width=700, offcut=True, prefix='OFF')
        production = self._make_production()
        job = self.env['td.mebli.cutting.job'].create({'production_ids': [(6, 0, production.ids)]})
        job.action_send()
        payload = job._td_simulate_optimizer()
        body_sheets = [s for s in payload['sheets'] if s['product_id'] == self.board_a.id]
        self.assertEqual(body_sheets[0]['lot_id'], offcut_lots.id)
        self.assertTrue(all(0 <= s['lot_id'] for s in body_sheets if s['lot_id']))

    def test_offcut_saving(self):
        self.board_a.standard_price = 100.0
        offcut_lot = self._add_lots(self.board_a, 1, length=1200, width=700, offcut=True, prefix='OFF')
        production = self._make_production()
        job = self.env['td.mebli.cutting.job'].create({'production_ids': [(6, 0, production.ids)]})
        job.action_send()
        job.action_simulate()
        used = sum(job.sheet_ids.filtered(lambda sheet: sheet.lot_id == offcut_lot).mapped('used_area_m2'))
        self.assertGreater(used, 0.0)
        self.assertAlmostEqual(job.offcut_used_m2, used, places=2)
        self.assertAlmostEqual(job.offcut_saving, used * 100.0, places=2)

    def test_cutting_map_and_message(self):
        """The cutting map is drawn for every sheet; the chatter names the source in words, not as a key."""
        production = self._make_production()
        job = self.env['td.mebli.cutting.job'].create({'production_ids': [(6, 0, production.ids)]})
        job.action_send()
        job.action_simulate()
        self.assertEqual(str(job.map_html).count('<svg'), len(job.sheet_ids))
        self.assertIn('<rect', str(job.sheet_ids[:1].map_html))
        body = ' '.join(job.message_ids.mapped('body'))
        self.assertNotIn('simulated', body)
        self.assertIn(job.name.replace('/', '-'), job.export_attachment_id.name)
