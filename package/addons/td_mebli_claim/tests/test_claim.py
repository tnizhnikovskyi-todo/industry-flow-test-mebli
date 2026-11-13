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
            'td_part_id': part.id, 'under_warranty': True,
            'tag_ids': [(0, 0, {'name': 'Production defect'})]})
        self.assertEqual(claim.tag_ids.name, 'Production defect')  # the reason is the standard tag
        self.assertEqual(order.td_claim_count, 1)
        with self.assertRaises(UserError):  # a bought product is ordered again, not remade
            claim.action_td_remake()
        claim.product_id = self.cabinet
        claim.action_td_remake()
        self.assertEqual(claim.td_remake_production_id.product_id, self.cabinet)
        self.assertIn(claim.name, claim.td_remake_production_id.origin)


@tagged('post_install', '-at_install')
class TestPaidRepair(TdMebliSaleCommon):
    """F-55: after the warranty the repair is paid: the standard «Under Warranty» is off, the quotation invoices."""

    def test_after_warranty_the_customer_pays(self):
        from datetime import timedelta
        from odoo import fields
        order = self._make_order()
        order.action_confirm()
        order.flush_recordset()
        old = fields.Datetime.now() - timedelta(days=800)
        self.env.cr.execute('UPDATE sale_order SET effective_date = %s WHERE id = %s', (old, order.id))
        order.invalidate_recordset(['effective_date'])
        claim = self.env['repair.order'].create({'partner_id': self.partner.id, 'product_id': self.cabinet.id,
                                                 'td_claim_order_id': order.id})
        self.assertTrue(claim.td_after_warranty)
        self.assertLess(claim.td_warranty_end, fields.Date.today(), "24 months after the delivery")
        self.assertFalse(claim.under_warranty, "the standard flag: parts are not at price 0")
        recent = self.env['repair.order'].create({'partner_id': self.partner.id, 'product_id': self.cabinet.id,
                                                  'td_claim_order_id': self._confirmed_recent().id})
        self.assertTrue(recent.under_warranty)

    def _confirmed_recent(self):
        order = self._make_order()
        order.action_confirm()
        return order
