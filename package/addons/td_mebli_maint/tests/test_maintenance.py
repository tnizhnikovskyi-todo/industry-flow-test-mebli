from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMaintenance(TransactionCase):
    """Position 22 (F-60): a breakdown writes the downtime of the section in the standard time log of the work center."""

    def test_breakdown_downtime_in_the_work_center_log(self):
        env = self.env
        center = env['mrp.workcenter'].create({'name': 'Edge banding'})
        machine = env['maintenance.equipment'].create({'name': 'Edge bander', 'td_workcenter_id': center.id})
        request = env['maintenance.request'].create({'name': 'Glue unit overheats', 'equipment_id': machine.id,
                                                     'maintenance_type': 'corrective'})
        self.assertEqual(request.td_workcenter_id, center)
        request.action_td_start_downtime()
        row = request.td_downtime_id
        self.assertEqual(row.workcenter_id, center)
        self.assertEqual(row.loss_id, env.ref('mrp.block_reason1'))
        self.assertTrue(request.td_downtime_open)
        self.assertEqual(center.td_request_open_count, 1)
        done = env['maintenance.stage'].search([('done', '=', True)], limit=1)
        request.stage_id = done
        self.assertTrue(row.date_end, "closing the request ends the downtime")
        self.assertFalse(request.td_downtime_open)

    def test_downtime_needs_a_work_center(self):
        machine = self.env['maintenance.equipment'].create({'name': 'Drill without a section'})
        request = self.env['maintenance.request'].create({'name': 'Spindle noise', 'equipment_id': machine.id,
                                                          'maintenance_type': 'corrective'})
        with self.assertRaises(UserError):
            request.action_td_start_downtime()
        self.assertFalse(request.td_downtime_id, "no downtime row without a section")
