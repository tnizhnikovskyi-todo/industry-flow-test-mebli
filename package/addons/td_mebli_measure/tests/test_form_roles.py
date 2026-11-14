from odoo.tests import HttpCase, tagged
from odoo.tools.safe_eval import safe_eval


@tagged('post_install', '-at_install')
class TestMeasureFormRoles(HttpCase):
    """D-03 (A-11-7): the form of the measurement sheet opened in the browser under every role of A-16 (measurer,
    salesperson, technologist, finance, owner). The unit tests did not see the error: «options» of a field are evaluated
    by the web client without the record (web/views/fields/field.js), so a name of a field there breaks the form."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        partner = env['res.partner'].create({'name': 'Form roles customer'})
        cls.lead = env['crm.lead'].create({'name': 'Kitchen', 'type': 'opportunity', 'partner_id': partner.id})
        cls.order = env['sale.order'].create({'partner_id': partner.id, 'opportunity_id': cls.lead.id})
        roles = {
            'measurer': ['td_mebli_measure.group_td_mebli_measurer'],
            'salesman': ['sales_team.group_sale_salesman'],
            'technologist': ['mrp.group_mrp_user'],
            'finance': ['sales_team.group_sale_salesman_all_leads', 'td_mebli_base.group_finance'],
            'owner': ['sales_team.group_sale_manager', 'mrp.group_mrp_manager', 'td_mebli_base.group_finance'],
        }
        cls.users = {}
        for role, groups in roles.items():
            cls.users[role] = env['res.users'].with_context(no_reset_password=True).create({
                'name': f'Form {role}', 'login': f'td_form_{role}', 'password': f'td_form_{role}',
                'group_ids': [(6, 0, [env.ref(group).id for group in groups])]})
        cls.order.user_id = cls.users['salesman']  # the salesperson sees the sheets of his own orders
        cls.sheet = env['td.mebli.measure'].create({
            'room': 'Kitchen', 'measurer_id': cls.users['measurer'].id, 'lead_id': cls.lead.id, 'order_id': cls.order.id,
            'niche_ids': [(0, 0, {'name': 'Fridge niche', 'width_mm': 600, 'height_mm': 2000, 'depth_mm': 600})]})

    def test_options_are_literals(self):
        """The web client evaluates «options» without the record: only literals there (true/false of JS too)."""
        for role, user in self.users.items():
            arch = self.env['td.mebli.measure'].with_user(user).get_views([(False, 'form')])['views']['form']['arch']
            for value in __import__('re').findall(r'options="([^"]*)"', arch):
                value = value.replace('&quot;', '"').replace('&apos;', "'")
                safe_eval(value, {'true': True, 'false': False, 'null': None})  # a name of a field raises here

    def test_form_opens_for_every_role(self):
        for role in self.users:
            with self.subTest(role=role):
                self.start_tour(f'/odoo/action-td_mebli_measure.td_mebli_measure_my_action/{self.sheet.id}',
                                'td_mebli_measure_form_tour', login=f'td_form_{role}')
