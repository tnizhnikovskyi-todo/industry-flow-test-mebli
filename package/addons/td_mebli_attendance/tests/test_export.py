import base64
from datetime import datetime

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTimesheetExport(TransactionCase):
    """Position 23 (F-61): the time sheet from the standard attendances into a file for BAS (imitation)."""

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
        self.assertTrue(text.startswith('#'), "the file says it is an imitation")
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
