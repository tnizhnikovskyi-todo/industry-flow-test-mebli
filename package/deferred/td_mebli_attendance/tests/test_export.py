import base64
from datetime import datetime

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTimesheetExport(TransactionCase):
    """Position 23 (F-61, AC-078): the time sheet from the standard attendances into a file for BAS."""

    def test_hours_by_employee(self):
        env = self.env
        env.user.tz = 'Europe/Kyiv'
        worker = env['hr.employee'].create({'name': 'Cutter', 'pin': '1234', 'barcode': '0007'})
        for day in (3, 4):
            env['hr.attendance'].create({'employee_id': worker.id, 'check_in': datetime(2026, 11, day, 6, 0),
                                         'check_out': datetime(2026, 11, day, 15, 0)})
        wizard = env['td.mebli.timesheet.export'].create({'date_from': '2026-11-01', 'date_to': '2026-11-30'})
        wizard.action_build()
        line = wizard.line_ids.filtered(lambda l: l.employee_id == worker)
        # 9 h on site a day minus the lunch break of the working calendar (standard worked_hours)
        self.assertEqual((line.days, round(line.hours)), (2, 16))
        text = base64.b64decode(wizard.file).decode('utf-8-sig')
        self.assertIn('Cutter', text)
        self.assertTrue(text.startswith('#'), "the file says its format is the draft of the exchange contract")
        self.assertTrue(wizard.filename.endswith('.csv'))

    def test_attendance_manager_without_hr_rights(self):
        """The finance manager has Attendances rights only: the personnel code (an HR field) is read by the export."""
        env = self.env
        user = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Finance', 'login': 'td_fin', 'tz': 'Europe/Kyiv',
            'group_ids': [(6, 0, [env.ref('base.group_user').id, env.ref('hr_attendance.group_hr_attendance_manager').id])]})
        worker = env['hr.employee'].create({'name': 'Edge operator', 'barcode': '0042'})
        env['hr.attendance'].create({'employee_id': worker.id, 'check_in': datetime(2026, 11, 3, 6, 0),
                                     'check_out': datetime(2026, 11, 3, 15, 0)})
        wizard = env['td.mebli.timesheet.export'].with_user(user).create({'date_from': '2026-11-01', 'date_to': '2026-11-30'})
        wizard.action_build()
        self.assertIn('0042', base64.b64decode(wizard.file).decode('utf-8-sig'))

    def test_no_code_is_skipped_and_formulas_are_text(self):
        env = self.env
        env.user.tz = 'Europe/Kyiv'
        nameless = env['hr.employee'].create({'name': 'No badge'})
        tricky = env['hr.employee'].create({'name': '=HYPERLINK("http://x")', 'barcode': '+0013'})
        for employee in (nameless, tricky):
            env['hr.attendance'].create({'employee_id': employee.id, 'check_in': datetime(2026, 11, 3, 6, 0),
                                         'check_out': datetime(2026, 11, 3, 15, 0)})
        wizard = env['td.mebli.timesheet.export'].create({'date_from': '2026-11-01', 'date_to': '2026-11-30'})
        wizard.action_build()
        text = base64.b64decode(wizard.file).decode('utf-8-sig')
        self.assertNotIn('No badge', text, "no personnel code: not in the file")
        self.assertNotIn(';%s;' % nameless.id, text, "never the database id instead of the code")
        self.assertIn('No badge', wizard.warning)
        self.assertTrue(wizard.line_ids.filtered(lambda l: l.employee_id == nameless).skipped)
        self.assertIn("'=HYPERLINK", text, "a formula is written as text")
        self.assertIn("'+0013", text)
        self.assertNotIn(';=', text)

    def test_ac_078_file_columns_and_total(self):
        """AC-078: CSV of the draft contract — employee, personnel code, days, hours — with the total of the hours."""
        env = self.env
        env.user.tz = 'Europe/Kyiv'
        first = env['hr.employee'].create({'name': 'Edge operator A', 'barcode': '0101'})
        second = env['hr.employee'].create({'name': 'Edge operator B', 'barcode': '0102'})
        for employee in (first, second):
            env['hr.attendance'].create({'employee_id': employee.id, 'check_in': datetime(2026, 11, 3, 6, 0),
                                         'check_out': datetime(2026, 11, 3, 10, 0)})
        wizard = env['td.mebli.timesheet.export'].create({'date_from': '2026-11-01', 'date_to': '2026-11-30'})
        wizard.action_build()
        rows = [line.split(';') for line in base64.b64decode(wizard.file).decode('utf-8-sig').splitlines()]
        self.assertEqual(rows[1], ['employee', 'personnel_code', 'period_from', 'period_to', 'days', 'hours'])
        data = {row[1]: row for row in rows[2:-1]}
        self.assertEqual((data['0101'][4], data['0101'][5]), ('1', '4.00'))
        self.assertEqual(rows[-1][0], '# total')
        self.assertAlmostEqual(float(rows[-1][5]), wizard.total_hours, places=2)
        self.assertAlmostEqual(float(rows[-1][5]), 8.0, places=2)
        self.assertFalse(wizard.warning)

    def test_ac_078_empty_period_gives_an_empty_file_with_a_warning(self):
        """AC-078: a period without attendances — an empty file (header and zero total) and a warning."""
        wizard = self.env['td.mebli.timesheet.export'].create({'date_from': '2020-02-01', 'date_to': '2020-02-29'})
        wizard.action_build()
        rows = base64.b64decode(wizard.file).decode('utf-8-sig').splitlines()
        self.assertEqual(len(rows), 3, "comment, header and the zero total only")
        self.assertTrue(rows[-1].endswith(';0.00'))
        self.assertIn('No attendances in the period', wizard.warning)
        self.assertFalse(wizard.line_ids)
