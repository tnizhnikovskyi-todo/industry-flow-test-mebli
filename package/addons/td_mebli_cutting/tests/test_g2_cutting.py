import base64

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TdMebliCuttingCommon


@tagged('post_install', '-at_install')
class TestG2Cutting(TdMebliCuttingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tech = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Technologist G2', 'login': 'td_tech_g2',
            'group_ids': [(6, 0, [cls.env.ref('mrp.group_mrp_user').id, cls.env.ref('stock.group_stock_user').id])]})

    def _job(self, productions):
        return self.env['td.mebli.cutting.job'].create({'production_ids': [(6, 0, productions.ids)]})

    # AC-028 -------------------------------------------------------------
    def test_ac_028_sent_version_date_and_fixed_file(self):
        production = self._make_production()
        job = self._job(production)
        job.action_send()
        self.assertEqual(job.state, 'sent')
        self.assertEqual(job.bom_version, '1')
        self.assertEqual(production.bom_id.td_cut_version, 1)
        self.assertTrue(job.sent_on)
        self.assertEqual(job.sent_by, self.env.user)
        content = base64.b64decode(job.export_attachment_id.datas).decode()
        self.assertIn(f'{production.name}-01', content)
        other = self.env['ir.attachment'].create({'name': 'x.csv', 'datas': base64.b64encode(b'x')})
        with self.assertRaisesRegex(UserError, 'does not change'):
            job.export_attachment_id = other
        # AC-052 through the cutting: the parts of the sent specification are locked
        with self.assertRaisesRegex(UserError, r'version 1\)'):
            production.bom_id.td_part_ids[0].length_mm = 100

    def test_ac_028_rpc_context_does_not_unlock_the_sent_file(self):
        """Review A-11: the context flag of a client (JSON-RPC can send `td_cutting_send: true`) does not lift the lock;
        only the private object of the module does (the send and the reset to draft use it)."""
        job = self._job(self._make_production())
        job.action_send()
        other = self.env['ir.attachment'].create({'name': 'x.csv', 'datas': base64.b64encode(b'x')})
        for value in (True, 1, 'CUTTING_SEND'):
            with self.assertRaisesRegex(UserError, 'does not change'):
                job.with_context(td_cutting_send=value).write({'export_attachment_id': other.id})
        part = job.production_ids.bom_id.td_part_ids[0]
        with self.assertRaisesRegex(UserError, r'version 1\)'):
            part.with_context(td_cut_unlock=True).length_mm = 100
        job.action_cancel()
        job.action_draft()  # the module itself still resets the file through its private object
        self.assertFalse(job.export_attachment_id)

    # AC-054 -------------------------------------------------------------
    def test_ac_054_manufacturing_order_without_parts(self):
        plain_bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.cabinet_tmpl.id, 'product_qty': 1.0,
            'bom_line_ids': [(0, 0, {'product_id': self.board_a.id, 'product_qty': 1.0})]})
        production = self.env['mrp.production'].create({
            'product_id': self.cabinet.id, 'product_qty': 1.0, 'bom_id': plain_bom.id,
            'product_uom_id': self.cabinet.uom_id.id})
        production.action_confirm()
        count = self.env['td.mebli.cutting.job'].search_count([])
        with self.assertRaisesRegex(UserError, rf'^There are no cutting parts in manufacturing order {production.name}$'):
            production.action_td_create_cutting_job()
        self.assertEqual(self.env['td.mebli.cutting.job'].search_count([]), count)

    # AC-056 -------------------------------------------------------------
    def test_ac_056_no_measurement_warns_and_sends(self):
        job = self._job(self._make_production())  # no sales order, no measurement sheet
        self.assertTrue(job.td_measure_missing)
        job.action_send()
        self.assertEqual(job.state, 'sent')
        self.assertTrue(any('The measurement is not filled in — the check is skipped' in (body or '')
                            for body in job.message_ids.mapped('body')))

    # AC-057 -------------------------------------------------------------
    def test_ac_057_batch_of_three_orders_of_one_decor(self):
        productions = self._make_production() | self._make_production() | self._make_production()
        Job = self.env['td.mebli.cutting.job'].with_user(self.tech)
        with self.assertRaisesRegex(UserError, 'Cutting Batches'):  # box A: one order per job
            Job.create({'production_ids': [(6, 0, productions.ids)]})
        self._feature('cutting_batch', user=self.tech)
        action = productions.with_user(self.tech).action_td_create_cutting_job()
        job = self.env['td.mebli.cutting.job'].browse(action['res_id'])
        self.assertEqual(job.production_ids, productions)
        self.assertEqual(job.part_ids, productions.bom_id.td_part_ids)
        for production in productions:
            parts = job.part_ids.filtered(lambda part: part.bom_id == production.bom_id)
            self.assertTrue(parts)
            self.assertEqual(parts.td_production_id, production)

    # AC-058 -------------------------------------------------------------
    def test_ac_058_different_boards_in_one_job(self):
        self._feature('cutting_batch', user=self.tech)
        first = self._make_production()
        bom = self.env['mrp.bom']._td_generate_order_bom(self.cabinet, self.dims,
                                                          self.val_b | self.val_f | self.val_e04 | self.val_fit)
        second = self.env['mrp.production'].create({'product_id': self.cabinet.id, 'product_qty': 1.0,
                                                    'bom_id': bom.id, 'product_uom_id': self.cabinet.uom_id.id})
        second.action_confirm()
        count = self.env['td.mebli.cutting.job'].search_count([])
        with self.assertRaisesRegex(UserError, r'^Only one board material in one cutting job\.$'), \
                self.env.cr.savepoint():  # the request is rolled back by the error
            (first | second).with_user(self.tech).action_td_create_cutting_job()
        self.assertEqual(self.env['td.mebli.cutting.job'].search_count([]), count)

    # AC-059 -------------------------------------------------------------
    def test_ac_059_minimum_from_the_company_and_box_a_keeps_no_offcuts(self):
        self.env.company.td_min_offcut_mm = 400
        production = self._make_production()
        job = self._job(production)
        self.assertEqual(job.min_offcut_mm, 400)
        self._feature('offcut', on=False)
        job.action_send()
        job.action_simulate()
        self.assertTrue(job.sheet_ids.offcut_ids)
        job.action_done()
        self.assertFalse(self.env['stock.lot'].search([('td_cutting_job_id', '=', job.id)]))

    # AC-060 -------------------------------------------------------------
    def test_ac_060_pick_an_offcut_for_a_part(self):
        production = self._make_production()
        job = self._job(production)
        side = production.bom_id.td_part_ids.filtered(lambda part: part.name == 'Side')
        self.assertEqual((side.length_mm, side.width_mm), (700, 500))
        big = self._add_lots(self.board_a, 1, length=1000, width=700, offcut=True, prefix='BIG')
        turned = self._add_lots(self.board_a, 1, length=600, width=800, offcut=True, prefix='TURN')
        small = self._add_lots(self.board_a, 1, length=650, width=650, offcut=True, prefix='SMALL')
        other = self._add_lots(self.board_b, 1, length=1000, width=1000, offcut=True, prefix='OTHER')
        action = side.with_context(td_job_id=job.id).action_td_pick_offcut()
        wizard = self.env['td.mebli.offcut.pick'].browse(action['res_id'])
        self.assertIn(big, wizard.candidate_ids)
        self.assertIn(turned, wizard.candidate_ids)  # fits turned by 90°
        self.assertNotIn(small, wizard.candidate_ids)
        self.assertNotIn(other, wizard.candidate_ids)
        self.assertNotIn(self.sheet_lots[0], wizard.candidate_ids)  # whole sheets are not offcuts
        wizard.lot_id = big
        wizard.action_reserve()
        big.invalidate_recordset()
        self.assertGreater(big.td_reserved_m2, 0)
        self.assertIn(production.name, big.td_reserved_for)
        wizard2 = self.env['td.mebli.offcut.pick'].create({'job_id': job.id, 'part_id': side.id})
        self.assertNotIn(big, wizard2.candidate_ids)  # reserved: no longer free

    # AC-131 -------------------------------------------------------------
    def _result_csv(self, job, extra=''):
        lines = ['sheet;material;sheet_length;sheet_width;lot;type;code;x;y;length;width;rotated']
        x = 0
        for production in job.production_ids:
            for code, part in job._td_part_codes(production):
                for _index in range(part.qty):
                    sheet = {self.board_a: 1, self.facade: 2, self.back: 3}[part.material_id]
                    material = part.material_id.default_code or part.material_id.name
                    lines.append(f'{sheet};{material};2800;2070;;part;{code};{x};0;{int(part.length_mm)};'
                                 f'{int(part.width_mm)};0')
                    x += 10
        lines.append('1;A;2800;2070;;offcut;;0;1500;2800;500;0')
        return ('\n'.join(lines) + '\n' + extra).encode()

    def _import(self, job, data):
        wizard = self.env['td.mebli.cutting.result.import'].create({
            'job_id': job.id, 'file': base64.b64encode(data), 'filename': 'result.csv'})
        return wizard.action_import()

    def test_ac_131_import_of_the_cutting_result(self):
        job = self._job(self._make_production())
        job.action_send()
        self._import(job, self._result_csv(job))
        self.assertEqual(job.state, 'result')
        self.assertEqual(job.result_source, 'imported')
        self.assertEqual(len(job.sheet_ids), 3)
        self.assertEqual(len(job.sheet_ids.placement_ids), sum(job.part_ids.mapped('qty')))
        self.assertEqual(len(job.sheet_ids.offcut_ids), 1)
        self.assertTrue(0 < job.waste_pct < 100)

    def test_ac_131_part_of_another_job_writes_nothing(self):
        job = self._job(self._make_production())
        job.action_send()
        data = self._result_csv(job, extra='1;A;2800;2070;;part;MO-FOREIGN-01;0;0;100;100;0\n')
        with self.assertRaisesRegex(UserError, r'^Part MO-FOREIGN-01 does not belong to the job$'):
            self._import(job, data)
        self.assertEqual(job.state, 'sent')
        self.assertFalse(job.sheet_ids)

    # AC-026 (VP-09) -----------------------------------------------------
    def test_ac_026_distributor_mode_is_visible_on_the_job(self):
        job = self._job(self._make_production())
        self.env.company.td_cutting_mode = 'distributor'
        self.assertEqual(job.td_cutting_mode, 'distributor')  # «Send to cutting» (own cutting) is hidden
