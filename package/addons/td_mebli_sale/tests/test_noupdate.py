import importlib.util

from odoo.tests import TransactionCase, tagged
from odoo.tools import convert_file
from odoo.tools.misc import file_path


def _migration():
    path = file_path('td_mebli_sale/migrations/19.0.1.1.1/post-migrate.py')
    spec = importlib.util.spec_from_file_location('td_post_migrate_td_mebli_sale', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@tagged('post_install', '-at_install')
class TestSaleNoupdate(TransactionCase):
    """Review A-14 (M2): the data of the module edited for the customer is noupdate — an update keeps the edits."""

    def test_noupdate_flag_and_post_migrate(self):
        migration = _migration()
        data = self.env['ir.model.data'].search([('module', '=', 'td_mebli_sale'), ('name', 'in', migration.XMLIDS)])
        self.assertEqual(len(data), len(migration.XMLIDS))
        self.assertTrue(all(data.mapped('noupdate')))
        # a database installed before 19.0.1.1.1: the flag was False — the post-migrate sets it
        data.write({'noupdate': False})
        data.flush_recordset()
        migration.migrate(self.env.cr, '19.0.1.1.0')
        data.invalidate_recordset()
        self.assertTrue(all(data.mapped('noupdate')))
        migration.migrate(self.env.cr, None)  # a new installation: nothing to do, no error

    def test_update_keeps_the_edit(self):
        """An update of the module (data file in mode «update») keeps the text of the letter edited on B-04."""
        record = self.env.ref('td_mebli_sale.mail_template_td_change_sign')
        record.subject = 'B-04 edit'
        convert_file(self.env, 'td_mebli_sale', 'data/mail_template_data.xml', {}, mode='update')
        record.invalidate_recordset()
        self.assertEqual(record.subject, 'B-04 edit')
