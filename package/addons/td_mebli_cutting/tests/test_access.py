from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import TdMebliCuttingCommon


@tagged('post_install', '-at_install')
class TestAccess(TdMebliCuttingCommon):

    def test_stock_user_readonly(self):
        production = self._make_production()
        job = self.env['td.mebli.cutting.job'].create({'production_ids': [(6, 0, production.ids)]})
        job.action_send()
        job.action_simulate()
        user = self.env['res.users'].create({
            'name': 'Storekeeper', 'login': 'td_storekeeper',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id, self.env.ref('stock.group_stock_user').id])]})
        job_as_user = job.with_user(user)
        self.assertEqual(job_as_user.name, job.name)
        with self.assertRaises(AccessError):
            job_as_user.action_done()
        with self.assertRaises(AccessError):
            job_as_user.write({'kerf_mm': 5})
