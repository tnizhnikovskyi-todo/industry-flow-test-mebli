from odoo.tests import HttpCase, tagged

from .common import TdMebliSaleCommon


@tagged('post_install', '-at_install')
class TestConfiguratorTour(HttpCase, TdMebliSaleCommon):

    def test_configurator_dimensions(self):
        self.start_tour('/odoo', 'td_mebli_sale_configurator_tour', login='admin')
        line = self.env['sale.order.line'].search([('product_id', '=', self.cabinet.id)], order='id desc', limit=1)
        self.assertEqual((line.td_width, line.td_height, line.td_depth), (1000, 700, 500))
        self.assertAlmostEqual(line.td_size_factor, (1000 * 700) / (800 * 700), places=3)
