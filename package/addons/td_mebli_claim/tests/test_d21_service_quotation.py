from odoo.exceptions import AccessError
from odoo.tests import tagged

from .test_claim import ClaimCommon


@tagged('post_install', '-at_install')
class TestD21ServiceQuotation(ClaimCommon):
    """D-21 (AC-112, T-06): the service (group «Service», no Sales rights) creates the quotation of the paid repair of a
    claim; the Inventory administrator without «Service» and Sales does not see the button and is refused."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        user = env.ref('base.group_user').id
        cls.service = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'D-21 service', 'login': 'td_d21_service',
            'group_ids': [(6, 0, [user, env.ref('project.group_project_user').id, env.ref('td_mebli_claim.group_service').id])]})
        cls.store = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'D-21 store', 'login': 'td_d21_store',
            'group_ids': [(6, 0, [user, env.ref('stock.group_stock_manager').id, env.ref('mrp.group_mrp_user').id])]})
        cls.salesman = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'D-21 salon', 'login': 'td_d21_salon',
            'group_ids': [(6, 0, [user, env.ref('sales_team.group_sale_salesman').id,
                                  env.ref('stock.group_stock_user').id])]})

    def _paid_claim(self):
        order = self._confirmed()
        order.user_id = self.salesman
        claim = self.env['repair.order'].with_user(self.service).create({
            'partner_id': self.partner.id, 'td_claim_order_id': order.id, 'product_id': self.cabinet.id,
            'under_warranty': False})
        return claim, order

    def test_service_creates_the_quotation(self):
        self.assertFalse(self.service.has_group('sales_team.group_sale_salesman'))
        claim, order = self._paid_claim()
        self.assertFalse(claim.under_warranty)
        result = claim.with_user(self.service).action_create_sale_order()
        self.assertTrue(result, "the form of the claim is reloaded (the service does not open the quotation)")
        quotation = claim.sale_order_id
        self.assertTrue(quotation)
        self.assertEqual(quotation.state, 'draft')
        self.assertEqual(quotation.partner_id, self.partner)
        self.assertEqual(quotation.origin, claim.name)
        self.assertEqual(quotation.create_uid, self.service, "the author is the service user")
        self.assertEqual(quotation.user_id, order.user_id, "the salesperson of the claimed order")
        self.assertIn(quotation.name, claim.message_ids[:1].body)
        self.assertEqual(claim.message_ids[:1].author_id, self.service.partner_id)
        # the salesperson finds it among his own quotations
        self.assertIn(quotation, self.env['sale.order'].with_user(self.salesman).search([('id', '=', quotation.id)]))

    def test_store_has_no_button_and_is_refused(self):
        claim, _order = self._paid_claim()
        for user, shown in ((self.service, True), (self.salesman, True), (self.store, False)):
            arch = self.env['repair.order'].with_user(user).get_views([(False, 'form')])['views']['form']['arch']
            self.assertEqual('name="action_create_sale_order"' in arch, shown, user.name)
        with self.assertRaises(AccessError):
            claim.with_user(self.store).action_create_sale_order()
        self.assertFalse(claim.sale_order_id)

    def test_salesperson_goes_the_standard_way(self):
        claim, _order = self._paid_claim()
        action = claim.with_user(self.salesman).action_create_sale_order()
        self.assertEqual(action['res_model'], 'sale.order')
        self.assertEqual(claim.sale_order_id.create_uid, self.salesman)
