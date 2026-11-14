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

    def test_d13_new_job_name_in_ukrainian(self):
        """D-13 (AC-N.01): a new cutting job shows «Новий» in uk_UA until it gets its number."""
        self.env['res.lang']._activate_lang('uk_UA')
        Job = self.env['td.mebli.cutting.job'].with_context(lang='uk_UA')
        self.assertEqual(Job.default_get(['name'])['name'], 'Новий')
        production = self._make_production()
        job = Job.create({'production_ids': [(6, 0, production.ids)]})
        self.assertNotIn(job.name, ('New', 'Новий'), "the number of the sequence is given on create")
