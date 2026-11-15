from odoo.exceptions import AccessError
from odoo.tests import Form, tagged

from .common import TdMebliCommon


@tagged('post_install', '-at_install')
class TestD20Technologist(TdMebliCommon):
    """D-20 (tr/security.md §1-2, ROLE-01): the group «Technologist» keeps the part rules and the import templates and
    sees them in «Manufacturing → Configuration»; the Manufacturing user without it keeps reading the rules only."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.tech = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'D-20 technologist', 'login': 'td_d20_tech',
            'group_ids': [(6, 0, [env.ref('base.group_user').id, env.ref('td_mebli_mrp.group_technologist').id])]})
        cls.mrp_user = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'D-20 shop', 'login': 'td_d20_shop',
            'group_ids': [(6, 0, [env.ref('base.group_user').id, env.ref('mrp.group_mrp_user').id])]})

    def test_group_implies_manufacturing_and_inventory_users(self):
        self.assertTrue(self.tech.has_group('mrp.group_mrp_user'))
        self.assertTrue(self.tech.has_group('stock.group_stock_user'))
        self.assertFalse(self.tech.has_group('mrp.group_mrp_manager'))

    def test_menus_of_the_technologist(self):
        visible = self.env['ir.ui.menu'].with_user(self.tech)._visible_menu_ids()
        for xmlid in ('mrp.menu_mrp_configuration', 'td_mebli_mrp.td_mebli_part_rule_menu',
                      'td_mebli_mrp.td_mebli_import_template_menu'):
            self.assertIn(self.env.ref(xmlid).id, visible, xmlid)
        self.assertNotIn(self.env.ref('mrp.menu_mrp_config').id, visible, "the settings stay with the administrator")
        shop = self.env['ir.ui.menu'].with_user(self.mrp_user)._visible_menu_ids()
        self.assertNotIn(self.env.ref('td_mebli_mrp.td_mebli_part_rule_menu').id, shop)

    def test_technologist_keeps_the_part_rules(self):
        """«New» in the list of the part rules: created, changed, deleted by the technologist (form of the web client)."""
        Rule = self.env['td.mebli.part.rule'].with_user(self.tech)
        with Form(Rule) as form:
            form.product_tmpl_id = self.cabinet_tmpl
            form.name = 'Shelf'
            form.len_w = 1.0
            form.len_const = -36.0
            form.wid_d = 1.0
        rule = form.record
        self.assertEqual(rule.product_tmpl_id, self.cabinet_tmpl)
        rule.write({'len_const': -40.0})
        rule.unlink()
        with self.assertRaises(AccessError):
            self.cabinet_tmpl.td_part_rule_ids[:1].with_user(self.mrp_user).write({'name': 'Not mine'})

    def test_technologist_keeps_the_import_templates(self):
        Template = self.env['td.mebli.import.template'].with_user(self.tech)
        template = Template.create({'name': 'CAD export', 'header_signature': 'part|length|width|qty',
                                    'mapping_json': {'part': 'name'}})
        template.write({'name': 'CAD export 2'})
        template.unlink()
