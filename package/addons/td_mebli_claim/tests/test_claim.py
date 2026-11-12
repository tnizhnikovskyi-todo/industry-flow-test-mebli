from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.td_mebli_sale.tests.common import TdMebliSaleCommon


@tagged('post_install', '-at_install')
class TestClaim(TdMebliSaleCommon):

    def test_claim_on_the_order_and_remake(self):
        order = self._make_order()
        order.action_confirm()
        part = order.order_line.td_bom_id.td_part_ids[:1]
        bought = self.env['product.product'].create({'name': 'Painted front', 'type': 'consu'})
        claim = self.env['repair.order'].create({
            'partner_id': self.partner.id, 'product_id': bought.id, 'td_claim_order_id': order.id,
            'td_part_id': part.id, 'td_reason': 'production', 'td_payer': 'company'})
        self.assertEqual(order.td_claim_count, 1)
        with self.assertRaises(UserError):  # a bought product is ordered again, not remade
            claim.action_td_remake()
        claim.product_id = self.cabinet
        claim.action_td_remake()
        self.assertEqual(claim.td_remake_production_id.product_id, self.cabinet)
        self.assertIn(claim.name, claim.td_remake_production_id.origin)
