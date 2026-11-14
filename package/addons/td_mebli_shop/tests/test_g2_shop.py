import re
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from odoo.addons.td_mebli_sale.tests.common import TdMebliSaleCommon



@tagged('post_install', '-at_install')
class TestG2Shop(TdMebliSaleCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.registry_enter_test_mode_cls()  # the wrong PIN counter is written in a cursor of its own (AC-071)
        cls.worker = cls.env['hr.employee'].create({'name': 'Worker G2', 'pin': '4321'})
        cls.order = cls._make_order()
        cls.order.action_confirm()
        cls.production = cls.order.mrp_production_ids[:1]
        cls.workorder = cls.production.workorder_ids[:1]

    def _feature(self, name, on=True):
        group = self.env.ref(f'td_mebli_base.group_feature_{name}')
        self.env.user.write({'group_ids': [(4 if on else 3, group.id)]})

    def _kiosk(self, action, pin='4321', **vals):
        return self.env['td.mebli.kiosk'].create({'workorder_id': self.workorder.id, 'action': action,
                                                  'employee_id': self.worker.id, 'pin': pin, **vals}).action_confirm()

    def _re(self, text, *args):
        """The message as the user sees it (translated to the language of the test user), as an exact regex."""
        return '^' + re.escape(self.env._(text, *args)) + '$'

    def _counter(self):
        self.env.cr.execute("SELECT td_pin_fail_count, td_pin_locked_until FROM hr_employee WHERE id = %s",
                            [self.worker.id])
        return self.env.cr.fetchone()

    # AC-071 -------------------------------------------------------------
    def test_ac_071_five_wrong_pins_lock_for_15_minutes_in_the_database(self):
        registry = self.env.registry
        opened = []
        test_cursor = registry.cursor  # the test cursor wrapper of the registry test mode

        def counting_cursor(*args, **kwargs):
            opened.append(1)
            return test_cursor(*args, **kwargs)
        with patch.object(registry, 'cursor', counting_cursor):
            for attempt in range(1, 5):
                with self.assertRaisesRegex(UserError, self._re("Wrong PIN")):
                    self._kiosk('start', pin='0000')
                self.assertEqual(self._counter()[0], attempt)
            self.assertEqual(len(opened), 4)  # every failure is written in a transaction of its own
            before = fields.Datetime.now()
            with self.assertRaisesRegex(UserError, self._re("Wrong PIN")):
                self._kiosk('start', pin='0000')
            count, locked_until = self._counter()
            self.assertEqual(count, 0)
            self.assertAlmostEqual(locked_until, before + timedelta(minutes=15), delta=timedelta(seconds=30))
            # locked: even the right PIN is refused, with the time of the end of the lock
            with self.assertRaisesRegex(UserError, self._re("The worker is locked until %s", '@@').replace('@@', r'\d\d:\d\d')):
                self._kiosk('start')
        # the lock is over: the right PIN works and clears the counter
        self.env.cr.execute("UPDATE hr_employee SET td_pin_locked_until = %s, td_pin_fail_count = 2 WHERE id = %s",
                            [fields.Datetime.now() - timedelta(minutes=1), self.worker.id])
        self.worker.invalidate_recordset()
        self._kiosk('start')
        self.assertEqual(self.workorder.state, 'progress')
        self.env.flush_all()
        self.assertEqual(self._counter(), (0, None))

    # A-14 security 1, 7 (CHECKS 4, 18) ------------------------------------
    def _pin_in_db(self, line):
        self.env.flush_all()
        self.env.cr.execute("SELECT pin FROM td_mebli_kiosk WHERE id = %s", [line.id])
        return self.env.cr.fetchone()[0]

    def test_pin_is_not_kept_and_not_read_by_another_user(self):
        mrp_user = self.env.ref('mrp.group_mrp_user')
        tablet, master = (self.env['res.users'].with_context(no_reset_password=True).create({
            'name': name, 'login': name, 'group_ids': [(6, 0, [mrp_user.id])]}) for name in ('td_tablet2', 'td_master2'))
        # the tablet saved the form (web_save) but has not pressed the button yet: only its own user reads the line
        line = self.env['td.mebli.kiosk'].with_user(tablet).create({
            'workorder_id': self.workorder.id, 'action': 'start', 'employee_id': self.worker.id, 'pin': '4321'})
        self.assertFalse(self.env['td.mebli.kiosk'].with_user(master).search([('id', '=', line.id)]))
        with self.assertRaises(AccessError):
            line.with_user(master).read(['pin', 'employee_id'])
        # a wrong PIN: the attempt is rolled back, the typed PIN is erased anyway (own transaction)
        wrong = self.env['td.mebli.kiosk'].with_user(tablet).create({
            'workorder_id': self.workorder.id, 'action': 'start', 'employee_id': self.worker.id, 'pin': '0000'})
        with self.assertRaisesRegex(UserError, self._re("Wrong PIN")):
            wrong.action_confirm()
        self.assertIsNone(self._pin_in_db(wrong))
        # the right PIN: the work is started and the PIN is erased too
        line.action_confirm()
        self.assertEqual(self.workorder.state, 'progress')
        self.assertIsNone(self._pin_in_db(line))
        self.assertFalse(line.with_user(tablet).pin)

    # AC-073 -------------------------------------------------------------
    def test_ac_073_scrap_makes_a_repeat_part_and_a_non_conformity(self):
        part = self.production.bom_id.td_part_ids[0]
        with self.assertRaisesRegex(UserError, 'workshop kiosk'):  # box A: no scrap at the workplace
            self._kiosk('scrap', scrap_part_id=part.id, scrap_reason='Chip on the edge')
        self._feature('kiosk')
        with self.assertRaisesRegex(UserError, 'reason'):
            self._kiosk('scrap', scrap_part_id=part.id, scrap_reason=' ')
        before = self.env['mrp.production'].search([])
        self._kiosk('scrap', scrap_part_id=part.id, scrap_reason='Chip on the edge')
        repeat = self.env['mrp.production'].search([]) - before
        self.assertEqual(len(repeat), 1)
        self.assertEqual(repeat.product_id, self.env.ref('td_mebli_shop.product_td_repeat_part'))
        self.assertIn(self.production.name, repeat.origin)
        self.assertIn(self.workorder.name, repeat.origin)
        self.assertEqual(repeat.bom_id.td_part_ids.mapped('name'), [part.name])
        self.assertEqual(repeat.bom_id.td_part_ids.material_id, part.material_id)
        self.assertEqual(repeat.state, 'confirmed')
        self.assertIn('Chip on the edge', repeat.message_ids.mapped('body')[0])
        check = self.workorder.td_quality_ids.filtered(lambda c: c.kind == 'scrap')
        self.assertEqual(len(check), 1)
        self.assertEqual((check.result, check.note, check.repeat_production_id, check.employee_id),
                         ('fail', 'Chip on the edge', repeat, self.worker))
        self.assertEqual(check.company_id, self.production.company_id)
        # the scrap is a non-conformity of the part, not the quality step: it does not block «Done»
        self.assertNotEqual(self.workorder.td_quality_state, 'fail')

    # AC-062 -------------------------------------------------------------
    def test_ac_062_scan_a_label_packs_the_line(self):
        self.order.action_td_build_kit()
        line = self.order.td_kit_line_ids.filtered('part_id')[0]
        other = self._make_order()
        other.action_confirm()
        other.action_td_build_kit()
        wizard = self.env['td.mebli.kit.scan'].create({'order_id': self.order.id})
        for code in ('UNKNOWN-1', other.td_kit_line_ids[0].label):
            wizard.code = code
            with self.assertRaisesRegex(UserError, r'^The label does not belong to this order$'):
                wizard.action_scan()
        self.assertFalse(self.order.td_kit_line_ids.filtered('packed'))
        self.assertFalse(other.td_kit_line_ids.filtered('packed'))
        wizard.code = line.label
        wizard.action_scan()
        self.assertTrue(line.packed)
        self.assertEqual(line.packed_by_id, self.env.user)
        self.assertEqual(self.order.td_kit_missing, len(self.order.td_kit_line_ids) - 1)
        self.assertFalse(wizard.code)

    # AC-093 -------------------------------------------------------------
    def test_ac_093_additional_order_of_a_missing_part(self):
        self.order.action_td_build_kit()
        line = self.order.td_kit_line_ids.filtered('part_id')[0]
        line.action_td_reorder()
        production = line.reorder_production_id
        self.assertTrue(production)
        self.assertEqual(production.origin, self.order.name)
        self.assertEqual(production.bom_id.td_part_ids.name, line.part_id.name)
        self.assertEqual(production.bom_id.td_part_ids.qty, int(line.qty))
        with self.assertRaisesRegex(UserError, 'already reordered'):
            line.action_td_reorder()
        fitting = self.order.td_kit_line_ids.filtered(lambda kit_line: not kit_line.part_id)[:1]
        if fitting:
            with self.assertRaisesRegex(UserError, 'is not a part'):
                fitting.action_td_reorder()

    # AC-133 -------------------------------------------------------------
    def test_ac_133_paper_sheet_and_done_afterwards(self):
        html, _kind = self.env['ir.actions.report']._render_qweb_html(
            'td_mebli_shop.report_workorder_sheet', self.production.ids)
        self.assertIn(b'td_mebli_report', html)
        for workorder in self.production.workorder_ids:
            self.assertIn(workorder.name.encode(), html)
        self.assertIn(f'{self.production.name}-01'.encode(), html)
        self.assertIn(b'data:image/', html)  # QR of the parts
        now = fields.Datetime.now()
        Backdate = self.env['td.mebli.workorder.backdate']
        future = Backdate.create({'workorder_id': self.workorder.id, 'reason': 'Power cut',
                                  'date_start': now - timedelta(hours=1), 'date_end': now + timedelta(hours=1)})
        with self.assertRaisesRegex(UserError, r'^The end date cannot be in the future$'):
            future.action_confirm()
        self.assertFalse(self.workorder.time_ids)
        start, end = now - timedelta(hours=5), now - timedelta(hours=3)
        Backdate.create({'workorder_id': self.workorder.id, 'reason': 'Power cut', 'date_start': start,
                         'date_end': end}).action_confirm()
        self.assertEqual(self.workorder.state, 'done')
        line = self.workorder.time_ids
        self.assertEqual(len(line), 1)
        self.assertEqual((line.date_start, line.date_end), (start.replace(microsecond=0), end.replace(microsecond=0)))
        self.assertEqual(line.description, 'Power cut')
        self.assertIn('Power cut', self.production.message_ids.mapped('body')[0])
