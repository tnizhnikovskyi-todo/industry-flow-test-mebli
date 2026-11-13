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
        with self.assertRaises(AccessError):  # a check is created only by the tablet after the PIN
            self.env['td.mebli.quality.check'].with_user(tablet).create({
                'workorder_id': self.workorder.id, 'name': 'Edge', 'result': 'fail', 'photo': PHOTO})
        self.env['td.mebli.kiosk'].with_user(tablet).create({
            'workorder_id': self.workorder.id, 'action': 'quality', 'employee_id': self.worker.id, 'pin': '1234',
            'result': 'fail', 'photo': PHOTO}).action_confirm()
        check = self.workorder.td_quality_ids[:1]
        self.assertEqual(check.employee_id, self.worker)
        with self.assertRaises(AccessError):  # the tablet records a check, it does not rewrite it
            check.with_user(tablet).write({'result': 'pass'})

    # N1: the work takes longer than planned — the standard splits the timer (mrp.workcenter.productivity._close copies
    # it with the loss «Reduced Speed»); the copy keeps the worker and must not fail for the tablet or a manufacturing user
    def _overrun(self, user, expected, back_minutes=30):
        from datetime import timedelta
        from odoo import fields
        self.workorder.duration_expected = expected
        loss = self.env['mrp.workcenter.productivity.loss'].search([('loss_type', '=', 'availability')], limit=1)

        def kiosk(action, **vals):
            self.env['td.mebli.kiosk'].with_user(user).create({
                'workorder_id': self.workorder.id, 'action': action, 'employee_id': self.worker.id, 'pin': '1234',
                **vals}).action_confirm()

        def age_open_line():  # the worker has been working for half an hour (longer than the plan)
            line = self.workorder.time_ids.filtered(lambda t: not t.date_end)
            line.sudo().write({'date_start': fields.Datetime.now() - timedelta(minutes=back_minutes)})
        kiosk('start'); age_open_line()
        kiosk('pause', loss_id=loss.id)
        kiosk('start'); age_open_line()
        kiosk('quality', photo=PHOTO, result='pass')
        kiosk('done')
        self.assertEqual(self.workorder.state, 'done')
        productive = self.workorder.time_ids.filtered(lambda t: t.loss_id.loss_type in ('productive', 'performance'))
        self.assertEqual(productive.td_employee_id, self.worker)  # every line of the work, the copies too
        self.assertFalse(self.workorder.time_ids.filtered(lambda t: not t.date_end))
        return self.workorder.time_ids

    def _user(self, login, groups):
        return self.env['res.users'].with_context(no_reset_password=True).create({
            'name': login, 'login': login, 'group_ids': [(6, 0, [self.env.ref(g).id for g in groups])]})

    def test_overrun_on_the_tablet_user(self):
        tablet = self._user('td_tablet_n1', ['mrp.group_mrp_user'])
        lines = self._overrun(tablet, expected=0.0)
        self.assertTrue(lines.filtered(lambda t: t.loss_type == 'performance'))

    def test_overrun_split_copies_the_worker(self):
        tablet = self._user('td_tablet_n1b', ['mrp.group_mrp_user'])
        lines = self._overrun(tablet, expected=10.0)  # 30 min of work against 10 planned: the timer is split
        performance = lines.filtered(lambda t: t.loss_type == 'performance')
        self.assertTrue(performance)
        self.assertEqual(performance.td_employee_id, self.worker)
        self.assertGreater(len(lines), 3)  # the split added copies

    def test_overrun_of_a_manufacturing_user(self):
        mrp_user = self._user('td_mrp_user_n1', ['mrp.group_mrp_user', 'stock.group_stock_user'])
        self.assertFalse(mrp_user.has_group('mrp.group_mrp_manager'))
        self._overrun(mrp_user, expected=10.0)

    def test_standard_finish_by_a_manufacturing_user_after_the_tablet(self):
        """The shop manager is away: a manufacturing user closes the work order with the standard button."""
        from datetime import timedelta
        from odoo import fields
        tablet = self._user('td_tablet_n1c', ['mrp.group_mrp_user'])
        mrp_user = self._user('td_mrp_user_n1c', ['mrp.group_mrp_user'])
        self.workorder.duration_expected = 10.0
        self.env['td.mebli.kiosk'].with_user(tablet).create({
            'workorder_id': self.workorder.id, 'action': 'start', 'employee_id': self.worker.id, 'pin': '1234'}).action_confirm()
        self.workorder.time_ids.sudo().write({'date_start': fields.Datetime.now() - timedelta(minutes=30)})
        self.workorder.with_user(mrp_user).end_all()
        self.assertEqual(self.workorder.time_ids.td_employee_id, self.worker)
        self.assertGreater(len(self.workorder.time_ids), 1)

    def test_copy_cannot_change_the_worker(self):
        from odoo.exceptions import AccessError
        tablet = self._user('td_tablet_n1d', ['mrp.group_mrp_user'])
        self.env['td.mebli.kiosk'].with_user(tablet).create({
            'workorder_id': self.workorder.id, 'action': 'start', 'employee_id': self.worker.id, 'pin': '1234'}).action_confirm()
        line = self.workorder.time_ids[:1]
        line.sudo().date_end = line.date_start  # a closed line (an open one cannot be doubled: the standard check)
        other = self.env['hr.employee'].create({'name': 'Other'})
        with self.assertRaises(AccessError):
            line.with_user(tablet).copy({'td_employee_id': other.id})
        self.assertEqual(line.with_user(tablet).copy().td_employee_id, self.worker)

    def test_worker_names_only_open_lines(self):
        loss = self.env['mrp.workcenter.productivity.loss'].search([('loss_type', '=', 'availability')], limit=1)
        self._kiosk('start')
        self.assertEqual(self.workorder.td_worker_names, 'Worker')
        self._kiosk('pause', loss_id=loss.id)
        self.assertFalse(self.workorder.td_worker_names)
