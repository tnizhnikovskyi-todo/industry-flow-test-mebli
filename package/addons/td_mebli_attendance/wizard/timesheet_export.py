import base64
import csv
import io
from collections import defaultdict
from datetime import datetime, time, timedelta

import pytz

from odoo import api, fields, models

FORMULA_START = ('=', '+', '-', '@', '\t', '\r')


def csv_safe(value):
    """A text cell that a spreadsheet would run as a formula (=, +, -, @) is written as text (CSV injection)."""
    text = '' if value is None else str(value)
    return "'" + text if text.startswith(FORMULA_START) else text


class TdMebliTimesheetExport(models.TransientModel):
    """Position 23 (F-61): the time sheet of the shop floor from the standard attendances (hr.attendance, checked in and
    out in the kiosk with a PIN) — hours by employee and day, exported to a CSV file for BAS. Imitation of the exchange:
    the file is made, nothing is sent."""
    _name = 'td.mebli.timesheet.export'
    _description = 'Time Sheet Export for BAS (imitation)'

    date_from = fields.Date(string='From', required=True,
                            default=lambda self: fields.Date.context_today(self).replace(day=1))
    date_to = fields.Date(string='To', required=True, default=fields.Date.context_today)
    line_ids = fields.One2many('td.mebli.timesheet.export.line', 'wizard_id', string='Time Sheet', readonly=True)
    file = fields.Binary(string='File for BAS', readonly=True, attachment=False)
    filename = fields.Char(string='File Name', readonly=True)
    total_hours = fields.Float(string='Hours in Total', compute='_compute_total', digits=(16, 1))
    warning = fields.Text(string='Not in the File', readonly=True,
                          help="Employees without a personnel code (Badge ID): BAS cannot match them, they are left out.")

    @api.depends('line_ids.hours')
    def _compute_total(self):
        for wizard in self:
            wizard.total_hours = sum(wizard.line_ids.mapped('hours'))

    def _td_rows(self):
        tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'Europe/Kyiv')
        start = tz.localize(datetime.combine(self.date_from, time.min)).astimezone(pytz.utc).replace(tzinfo=None)
        end = tz.localize(datetime.combine(self.date_to + timedelta(days=1), time.min)).astimezone(pytz.utc).replace(tzinfo=None)
        attendances = self.env['hr.attendance'].search([('check_in', '>=', start), ('check_in', '<', end),
                                                        ('check_out', '!=', False)])
        totals = defaultdict(lambda: [set(), 0.0])
        for attendance in attendances:
            day = pytz.utc.localize(attendance.check_in).astimezone(tz).date()
            totals[attendance.employee_id][0].add(day)
            totals[attendance.employee_id][1] += attendance.worked_hours
        return sorted(((employee, len(days), hours) for employee, (days, hours) in totals.items()),
                      key=lambda row: row[0].name)

    def action_build(self):
        self.ensure_one()
        rows = self._td_rows()
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=';')
        writer.writerow(['# ' + self.env._("Imitation of the exchange with BAS: the file is made, nothing is sent")])
        writer.writerow(['employee', 'personnel_code', 'period_from', 'period_to', 'days', 'hours'])
        skipped = []
        for employee, days, hours in rows:
            # sudo: the personnel code (badge) is an HR field; the officer of Attendances exports it, nothing is written
            code = employee.sudo().barcode
            if not code:
                skipped.append(employee)  # never the database id instead of the code: BAS would book it to someone else
                continue
            writer.writerow([csv_safe(employee.name), csv_safe(code), self.date_from, self.date_to, days, f'{hours:.2f}'])
        self.write({
            'line_ids': [(5, 0, 0)] + [(0, 0, {'employee_id': e.id, 'days': d, 'hours': h, 'skipped': e in skipped})
                                       for e, d, h in rows],
            'file': base64.b64encode(buffer.getvalue().encode('utf-8-sig')),
            'filename': self.env._("timesheet-BAS-imitation-%(start)s-%(end)s.csv", start=self.date_from, end=self.date_to),
            'warning': self.env._("No personnel code (Badge ID on the employee), not in the file: %s.",
                                  ', '.join(e.name for e in skipped)) if skipped else False,
        })
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': self.id, 'view_mode': 'form',
                'target': 'new', 'name': self.env._("Time Sheet for BAS (imitation)")}


class TdMebliTimesheetExportLine(models.TransientModel):
    _name = 'td.mebli.timesheet.export.line'
    _description = 'Time Sheet Line for BAS'

    wizard_id = fields.Many2one('td.mebli.timesheet.export', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    days = fields.Integer(string='Days')
    hours = fields.Float(string='Hours', digits=(16, 1))
    skipped = fields.Boolean(string='Not in the File', help="No personnel code: left out of the file.")
