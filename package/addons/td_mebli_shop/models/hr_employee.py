from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # AC-071 (AI-A08-12, R-11): wrong PINs of the shop tablet are counted in the database — the counter survives a
    # restart and several workers; written by the tablet in its own transaction (wizard/kiosk.py)
    td_pin_fail_count = fields.Integer(string='Wrong PINs in a Row', readonly=True, copy=False,
                                       groups='hr.group_hr_user')
    td_pin_locked_until = fields.Datetime(string='Tablet Locked until', readonly=True, copy=False,
                                          groups='hr.group_hr_user')
