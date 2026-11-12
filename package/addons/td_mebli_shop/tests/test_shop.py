from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.td_mebli_sale.tests.common import TdMebliSaleCommon

PHOTO = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='


@tagged('post_install', '-at_install')
class TestShop(TdMebliSaleCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.worker = cls.env['hr.employee'].create({'name': 'Worker', 'pin': '1234', 'hourly_cost': 150.0})
        cls.order = cls._make_order()
        cls.order.action_confirm()
        cls.workorder = cls.order.mrp_production_ids.workorder_ids[:1]
        cls.workorder.operation_id.td_quality_point = 'Edge without chips'

    def _kiosk(self, action, pin='1234', **vals):
        return self.env['td.mebli.kiosk'].create({'workorder_id': self.workorder.id, 'action': action,
                                                  'employee_id': self.worker.id, 'pin': pin, **vals}).action_confirm()

    def test_pin_start_pause_quality_done(self):
        with self.assertRaises(UserError):
            self._kiosk('start', pin='0000')
        self._kiosk('start')
        self.assertEqual(self.workorder.state, 'progress')
        self.assertEqual(self.workorder.time_ids.td_employee_id, self.worker)
        loss = self.env['mrp.workcenter.productivity.loss'].search([('loss_type', '=', 'availability')], limit=1)
        self._kiosk('pause', loss_id=loss.id)
        self.assertEqual(self.workorder.td_pause_reason, loss.name)
        self._kiosk('start')
        self.assertFalse(self.workorder.td_pause_reason)
        with self.assertRaises(UserError):  # «Done» needs the quality step with a photo first
            self._kiosk('done')
        self._kiosk('quality', photo=PHOTO, result='pass')
        self.assertEqual(self.workorder.td_quality_state, 'pass')
        self._kiosk('done')
        self.assertEqual(self.workorder.state, 'done')
        self.assertEqual(set(self.workorder.time_ids.td_employee_id.ids), {self.worker.id})

    def test_incomplete_set_does_not_leave(self):
        self.order.action_td_build_kit()
        lines = self.order.td_kit_line_ids
        self.assertTrue(lines)
        self.assertIn('fitting', lines.mapped('kind'))
        self.assertEqual(self.order.td_kit_missing, len(lines))
        picking = self.order.picking_ids.filtered(lambda p: p.picking_type_code == 'outgoing')[:1]
        if picking:
            with self.assertRaises(UserError):
                picking.button_validate()
        lines.action_td_pack()
        self.assertEqual(self.order.td_kit_missing, 0)

    def test_two_workers_through_the_kiosk(self):
        """In Community the timer belongs to the Odoo user (the shared tablet): a second worker must not continue the
        timer of the first one (his time would be lost) nor stop it with «Pause»."""
        second = self.env['hr.employee'].create({'name': 'Second', 'pin': '5678'})
        loss = self.env['mrp.workcenter.productivity.loss'].search([('loss_type', '=', 'availability')], limit=1)

        def kiosk(action, employee, pin, **vals):
            return self.env['td.mebli.kiosk'].create({'workorder_id': self.workorder.id, 'action': action,
                                                      'employee_id': employee.id, 'pin': pin, **vals}).action_confirm()
        self._kiosk('start')
        with self.assertRaisesRegex(UserError, 'one worker at a time'):
            kiosk('start', second, '5678')
        with self.assertRaisesRegex(UserError, 'one worker at a time'):
            kiosk('pause', second, '5678', loss_id=loss.id)
        with self.assertRaisesRegex(UserError, 'one worker at a time'):
            kiosk('done', second, '5678')
        open_lines = self.workorder.time_ids.filtered(lambda t: not t.date_end)
        self.assertEqual(open_lines.td_employee_id, self.worker)  # the timer of the first worker still runs
        self._kiosk('pause', loss_id=loss.id)
        kiosk('start', second, '5678')  # now the second worker takes it: his own time line
        productive = self.workorder.time_ids.filtered(lambda t: t.loss_type == 'productive')
        self.assertEqual(productive.td_employee_id, self.worker | second)
        self.assertEqual(len(productive.filtered(lambda t: not t.date_end)), 1)
        # the same worker cannot run two timers: another work order of the same order
        other = self.order.mrp_production_ids.workorder_ids[1:2]
        if other:
            with self.assertRaisesRegex(UserError, 'already working'):
                self.env['td.mebli.kiosk'].create({'workorder_id': other.id, 'action': 'start', 'employee_id': second.id,
                                                   'pin': '5678'}).action_confirm()

    def test_pin_errors_look_the_same(self):
        no_pin = self.env['hr.employee'].create({'name': 'No PIN'})
        messages = set()
        for employee, pin in ((no_pin, '1234'), (self.worker, '0000')):
            with self.assertRaises(UserError) as error:
                self.env['td.mebli.kiosk'].create({'workorder_id': self.workorder.id, 'action': 'start',
                                                   'employee_id': employee.id, 'pin': pin}).action_confirm()
            messages.add(str(error.exception))
        self.assertEqual(len(messages), 1)

    def test_worker_of_a_time_line_is_protected(self):
        from odoo.exceptions import AccessError
        tablet = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Tablet', 'login': 'td_tablet', 'group_ids': [(6, 0, [self.env.ref('mrp.group_mrp_user').id])]})
        self.workorder.with_user(tablet).check_access('read')
        self.env['td.mebli.kiosk'].with_user(tablet).create({
            'workorder_id': self.workorder.id, 'action': 'start', 'employee_id': self.worker.id, 'pin': '1234'}).action_confirm()
        line = self.workorder.time_ids[:1]
        self.assertEqual(line.td_employee_id, self.worker)
        other = self.env['hr.employee'].create({'name': 'Other'})
        with self.assertRaises(AccessError):
            line.with_user(tablet).write({'td_employee_id': other.id})
        check = self.env['td.mebli.quality.check'].with_user(tablet).create({
            'workorder_id': self.workorder.id, 'name': 'Edge', 'result': 'fail', 'photo': PHOTO})
        with self.assertRaises(AccessError):  # the tablet records a check, it does not rewrite it
            check.with_user(tablet).write({'result': 'pass'})
