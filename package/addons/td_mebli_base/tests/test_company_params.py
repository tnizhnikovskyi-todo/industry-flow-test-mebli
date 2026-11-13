from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged

from ..hooks import post_init_hook
from ..models.res_config_settings import TD_FEATURES


@tagged('post_install', '-at_install')
class TestCompanyParams(TransactionCase):
    """Parameters of the questionnaire on the company (SPEC §11), groups and the hook of td_mebli_base."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.salesman = new_test_user(cls.env, 'td_salesman', groups='sales_team.group_sale_salesman',
                                     company_id=cls.company.id)
        cls.margin = cls.env.ref('td_mebli_base.group_margin_view')

    def test_vp_defaults_of_the_company(self):
        """Defaults of SPEC §11.1 / §11.2; contract_mode «unset» = empty field (AC-033, AC-034)."""
        company = self.env['res.company'].create({'name': 'Furniture Ltd'})
        self.assertFalse(company.td_contract_mode)
        expected = {
            'td_payment_control': 'warn', 'td_pay_reminder_days': 2, 'td_margin_to_salesman': False,
            'td_cutting_mode': 'both', 'td_stuck_days': 5, 'td_price_threshold_pct': 5.0, 'td_min_offcut_mm': 300,
            'td_claim_overdue_days': 14, 'td_crew_split': 'equal', 'td_crew_base': 'final', 'td_crew_pct': 0.0,
            'td_install_in_price': False, 'td_legal_checked': False, 'td_box_profile': 'A',
        }
        self.assertEqual({name: company[name] for name in expected}, expected)
        self.assertEqual(sorted(dict(company._fields['td_contract_mode'].selection)), ['contract', 'sale'])

    def test_vp_ranges(self):
        """Closed ranges of SPEC §11.1 (VP-07, -10, -11, -12, -13)."""
        for name, bad in (('td_pay_reminder_days', 8), ('td_stuck_days', 0), ('td_price_threshold_pct', 51),
                          ('td_min_offcut_mm', 99), ('td_claim_overdue_days', 61)):
            with self.subTest(name=name), self.assertRaises(ValidationError):
                with self.env.cr.savepoint():
                    self.company.write({name: bad})
        self.company.write({'td_pay_reminder_days': 7, 'td_stuck_days': 30, 'td_min_offcut_mm': 1000})

    def test_settings_write_the_company(self):
        """The section «Furniture» of the settings edits the fields of the current company (related)."""
        settings = self.env['res.config.settings'].create({
            'td_contract_mode': 'sale', 'td_payment_control': 'block', 'td_stuck_days': 10,
            'td_price_threshold_pct': 7.0, 'td_crew_split': 'time', 'td_act_checklist': 'Fronts are level'})
        settings.execute()
        self.assertEqual((self.company.td_contract_mode, self.company.td_payment_control, self.company.td_stuck_days,
                          self.company.td_price_threshold_pct, self.company.td_crew_split),
                         ('sale', 'block', 10, 7.0, 'time'))
        self.assertEqual(self.company.td_act_checklist, 'Fronts are level')

    def test_ac_018_margin_group_follows_the_parameter(self):
        """AC-018: «Salesman Sees the Margin» off — the salesman has no «Sees the margin»; on — has; off again — removed;
        a salesman created later gets the group by the parameter of his company."""
        self.company.td_margin_to_salesman = False
        self.assertNotIn(self.margin, self.salesman.all_group_ids)
        self.company.td_margin_to_salesman = True
        self.assertIn(self.margin, self.salesman.all_group_ids)
        later = new_test_user(self.env, 'td_salesman2', groups='sales_team.group_sale_salesman',
                              company_id=self.company.id)
        self.assertIn(self.margin, later.all_group_ids)
        other = self.env['res.company'].create({'name': 'Other Ltd'})
        stranger = new_test_user(self.env, 'td_salesman3', groups='sales_team.group_sale_salesman',
                                 company_id=other.id, company_ids=[(6, 0, other.ids)])
        self.assertNotIn(self.margin, stranger.all_group_ids)  # the parameter of another company
        self.company.td_margin_to_salesman = False
        self.assertNotIn(self.margin, self.salesman.all_group_ids)
        self.assertNotIn(self.margin, later.all_group_ids)
        user = new_test_user(self.env, 'td_internal', groups='base.group_user', company_id=self.company.id)
        self.company.td_margin_to_salesman = True
        self.assertNotIn(self.margin, user.all_group_ids)  # not a salesman

    def test_ac_018_manual_grant_of_the_administrator_stays(self):
        """Review A-11: the parameter takes back only what it gave — «Sees the margin» given by an administrator by
        hand stays when the parameter is switched off."""
        self.company.td_margin_to_salesman = False
        manual = new_test_user(self.env, 'td_salesman_manual', groups='sales_team.group_sale_salesman',
                               company_id=self.company.id)
        manual.group_ids = [(4, self.margin.id)]  # the administrator gives the group by hand
        self.assertFalse(manual.td_margin_auto)
        self.company.td_margin_to_salesman = True
        self.assertTrue(self.salesman.td_margin_auto)
        self.assertFalse(manual.td_margin_auto, "the group was there before: not marked as given by the parameter")
        self.company.td_margin_to_salesman = False
        self.assertNotIn(self.margin, self.salesman.all_group_ids)  # given by the parameter — taken back
        self.assertIn(self.margin, manual.all_group_ids)  # given by hand — stays

    def test_ac_018_finance_group(self):
        """tr/security.md §1: «Finance» includes the standard invoicing group; both groups exist for the groups= of G1."""
        finance = self.env.ref('td_mebli_base.group_finance')
        self.assertIn(self.env.ref('account.group_account_invoice'), finance.all_implied_ids)
        self.assertEqual(finance.privilege_id, self.env.ref('td_mebli_base.res_groups_privilege_mebli'))

    def test_ac_111_warranty_of_the_category_is_empty(self):
        """AC-111 (G0 part): the warranty term lives on the category and is empty until the lawyer (No 17)."""
        category = self.env['product.category'].create({'name': 'Kitchens'})
        self.assertFalse(category.td_warranty_months)
        category.td_warranty_months = 24
        self.assertEqual(category.td_warranty_months, 24)
        with self.assertRaises(ValidationError):
            category.td_warranty_months = -1

    def test_ac_n07_feature_groups_off_in_box_a(self):
        """AC-N.07: the 11 feature groups of box B exist, are off after the installation (profile A) and are switched
        on and off by the checkboxes of the settings (implied by «Internal User»)."""
        employee = self.env.ref('base.group_user')
        groups = {key: self.env.ref('td_mebli_base.group_feature_%s' % key) for key in TD_FEATURES}
        self.assertEqual(len(groups), 11)
        for group in groups.values():
            self.assertNotIn(group, employee.all_implied_ids)
            self.assertNotIn(group, self.salesman.all_group_ids)
        self.env['res.config.settings'].create({'group_td_feature_kiosk': True, 'group_td_feature_nbu': True}).execute()
        self.assertIn(groups['kiosk'], self.salesman.all_group_ids)
        self.assertIn(groups['nbu'], self.salesman.all_group_ids)
        self.assertNotIn(groups['quality'], self.salesman.all_group_ids)
        values = self.env['res.config.settings'].default_get(['group_td_feature_kiosk', 'group_td_feature_quality'])
        self.assertEqual((values['group_td_feature_kiosk'], values['group_td_feature_quality']), (True, False))
        self.env['res.config.settings'].create({'group_td_feature_kiosk': False, 'group_td_feature_nbu': True}).execute()
        self.assertNotIn(groups['kiosk'], employee.all_implied_ids)

    def test_ac_n04_hook_moves_the_parameters(self):
        """post_init_hook: the system parameters of the slice (work → contract) and of the config package (td_mebli.vp_xx)
        become the fields of every company; wrong values are skipped."""
        param = self.env['ir.config_parameter'].sudo()
        category = self.env['product.category'].create({'name': 'Wardrobes'})
        other = self.env['res.company'].create({'name': 'Second Ltd'})
        param.set_param('td_mebli_sale.contract_mode', 'work')
        param.set_param('td_mebli_install.payment_control', 'block')
        param.set_param('td_mebli_claim.warranty_months', '24')
        param.set_param('td_mebli.vp_07', '3')
        param.set_param('td_mebli.vp_08', 'true')
        param.set_param('td_mebli.vp_11', '7')
        param.set_param('td_mebli.vp_14', 'time')
        param.set_param('td_mebli.vp_10', 'many')   # not a number: skipped
        post_init_hook(self.env)
        for company in self.company | other:
            self.assertEqual((company.td_contract_mode, company.td_payment_control, company.td_pay_reminder_days,
                              company.td_margin_to_salesman, company.td_price_threshold_pct, company.td_crew_split,
                              company.td_stuck_days),
                             ('contract', 'block', 3, True, 7.0, 'time', 5))
        self.assertEqual(category.td_warranty_months, 24)
        self.assertIn(self.margin, self.salesman.all_group_ids)
        param.set_param('td_mebli.contract_mode', 'unset')   # the answer of the config package wins over the slice
        post_init_hook(self.env)
        self.assertFalse(self.company.td_contract_mode)

    def test_ac_n04_hook_without_parameters_keeps_the_defaults(self):
        """No parameters of the slice: the mode stays unset (AC-034), the warranty stays empty (AC-111)."""
        param = self.env['ir.config_parameter'].sudo()
        for key in ('td_mebli_sale.contract_mode', 'td_mebli_install.payment_control', 'td_mebli_claim.warranty_months'):
            param.search([('key', '=', key)]).unlink()
        category = self.env['product.category'].create({'name': 'Hallways'})
        post_init_hook(self.env)
        self.assertFalse(self.company.td_contract_mode)
        self.assertEqual(self.company.td_payment_control, 'warn')
        self.assertFalse(category.td_warranty_months)
