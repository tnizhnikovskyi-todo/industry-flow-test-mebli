from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import TdMebliCommon


@tagged('post_install', '-at_install')
class TestPartRules(TdMebliCommon):

    def test_dims(self):
        side = self.cabinet_tmpl.td_part_rule_ids.filtered(lambda r: r.name == 'Side')
        self.assertEqual(side._compute_size(self.dims), (700.0, 500.0))
        door = self.cabinet_tmpl.td_part_rule_ids.filtered(lambda r: r.name == 'Door')
        self.assertEqual(door._compute_size(self.dims), (696.0, 396.0))
        # extreme dimensions
        small = {'width': 400, 'height': 500, 'depth': 300}
        self.assertEqual(door._compute_size(small), (496.0, 196.0))

    def test_non_positive_rule_rejected(self):
        with self.assertRaises(ValidationError), mute_logger('odoo.sql_db'):
            self.env['td.mebli.part.rule'].create({
                'product_tmpl_id': self.cabinet_tmpl.id, 'name': 'Bad', 'len_h': 1.0, 'len_const': -1000.0,
                'wid_d': 1.0})

    def test_limits_constraint(self):
        with self.assertRaises(ValidationError):
            self.cabinet_tmpl.td_width_nominal = 2000
