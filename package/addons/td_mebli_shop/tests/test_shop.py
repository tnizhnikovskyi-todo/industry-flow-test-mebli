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
