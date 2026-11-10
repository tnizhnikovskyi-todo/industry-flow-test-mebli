from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import TdMebliSaleCommon


@tagged('post_install', '-at_install')
class TestSaleLine(TdMebliSaleCommon):

    def test_dims_from_custom_values(self):
        line = self._make_order(width=1000, height=650, depth=450).order_line
        self.assertEqual((line.td_width, line.td_height, line.td_depth), (1000, 650, 450))
        self.assertAlmostEqual(line.td_size_factor, (1000 * 650) / (800 * 700), places=3)

    def test_invalid_dims(self):
        with self.assertRaises(ValidationError):
            self._make_order(width=5000)
        with self.assertRaises(ValidationError):
            self._make_order(raw={self.val_w: '12a'})

    def test_price(self):
        line = self._make_order(width=1000, height=700, body=self.val_b, edge=self.val_e2).order_line
        base = 1000.0 + 600.0 + 350.0
        self.assertAlmostEqual(line.price_unit, base * (1000 * 700) / (800 * 700), places=2)

    def test_manual_price_kept(self):
        line = self._make_order().order_line
        line.price_unit = 4321.0
        line.td_width = 1100
        self.assertEqual(line.price_unit, 4321.0)
