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

    def test_d23_technologist_prepares_products_and_specifications(self):
        """D-23 (A-11-fix5; decision of the owner 2026-11-16, rights of the technologist): ROLE-01 creates and changes the
        materials and the parametric product (template, attribute lines, extra prices), the work centers, the
        specification with its lines and operations — the standard «Manufacturing user» only reads them. Nothing of it is
        deleted by the technologist: deleting stays with the administrator."""
        env = self.env(user=self.tech)
        board = env['product.product'].create({'name': 'D-23 board', 'type': 'consu', 'is_storable': True})
        board.product_tmpl_id.write({'description_purchase': 'board 18 mm'})
        attribute = self.env['product.attribute'].create({'name': 'D-23 decor', 'value_ids': [
            (0, 0, {'name': 'White'}), (0, 0, {'name': 'Oak'})]})
        product = env['product.template'].create({'name': 'D-23 wardrobe', 'type': 'consu', 'attribute_line_ids': [
            (0, 0, {'attribute_id': attribute.id, 'value_ids': [(6, 0, attribute.value_ids.ids)]})]})
        ptav = product.attribute_line_ids.product_template_value_ids[:1]
        ptav.price_extra = 150.0
        center = env['mrp.workcenter'].create({'name': 'D-23 cutting', 'code': 'D23'})
        center.write({'time_efficiency': 90.0})
        bom = env['mrp.bom'].create({
            'product_tmpl_id': product.id, 'product_qty': 1.0,
            'bom_line_ids': [(0, 0, {'product_id': board.id, 'product_qty': 2.0})],
            'operation_ids': [(0, 0, {'name': 'Cut', 'workcenter_id': center.id, 'time_cycle_manual': 10.0})]})
        bom.bom_line_ids.product_qty = 3.0
        bom.operation_ids.time_cycle_manual = 12.0
        self.assertEqual((bom.bom_line_ids.product_qty, ptav.price_extra, bom.operation_ids.time_cycle_manual),
                         (3.0, 150.0, 12.0))
        for record in (bom.operation_ids, bom.bom_line_ids, bom, center, product, board):
            with self.assertRaises(AccessError):
                record.unlink()
        # D-24 (A-11-fix6): removing an attribute line is not a deletion for the technologist — the standard archives
        # the line when it cannot be deleted, its variants are archived (td_mebli_mrp), nothing is deleted
        line = product.attribute_line_ids
        line.unlink()
        self.assertTrue(line.exists())
        self.assertFalse(line.active)
        with self.assertRaises(AccessError):
            self.env(user=self.mrp_user)['mrp.bom'].create({'product_tmpl_id': product.id})

    def test_d24_technologist_keeps_exclusions_and_archives(self):
        """D-24 (A-11-fix6; decision of the owner 2026-11-16): the technologist keeps «Exclude for» of the values of a
        product — the exclusion is created and saved from the form of the value (web client), changed, not deleted; a
        variant left without a possible combination is archived, not deleted. The products, specifications,
        operations and work centers are archived by the technologist; deleting stays with the administrator."""
        env = self.env(user=self.tech)
        decor = self.env['product.attribute'].create({'name': 'D-24 decor', 'create_variant': 'no_variant', 'value_ids': [
            (0, 0, {'name': 'White'}), (0, 0, {'name': 'Oak'})]})
        size = self.env['product.attribute'].create({'name': 'D-24 size', 'create_variant': 'always', 'value_ids': [
            (0, 0, {'name': '600'}), (0, 0, {'name': '800'})]})
        color = self.env['product.attribute'].create({'name': 'D-24 color', 'create_variant': 'always', 'value_ids': [
            (0, 0, {'name': 'Red'}), (0, 0, {'name': 'Blue'})]})
        product = env['product.template'].create({'name': 'D-24 wardrobe', 'type': 'consu', 'attribute_line_ids': [
            (0, 0, {'attribute_id': decor.id, 'value_ids': [(6, 0, decor.value_ids.ids)]}),
            (0, 0, {'attribute_id': size.id, 'value_ids': [(6, 0, size.value_ids.ids)]}),
            (0, 0, {'attribute_id': color.id, 'value_ids': [(6, 0, color.value_ids.ids)]})]})
        self.assertEqual(len(product.product_variant_ids), 4)
        white, oak = product.attribute_line_ids[0].product_template_value_ids
        s600, s800 = product.attribute_line_ids[1].product_template_value_ids
        red = product.attribute_line_ids[2].product_template_value_ids[0]
        with Form(white.with_user(self.tech)) as form:  # the form of the value: tab «Exclude for»
            with form.exclude_for.new() as line:
                line.product_tmpl_id = product
                line.value_ids.add(s800)
        exclusion = white.exclude_for
        self.assertEqual((len(exclusion), exclusion.value_ids), (1, s800))
        exclusion.with_user(self.tech).write({'value_ids': [(4, s600.id)]})
        self.assertEqual(exclusion.value_ids, s600 | s800)
        self.assertEqual(len(product.product_variant_ids), 4, "a value without variants: the variants stay")
        with self.assertRaises(AccessError):
            exclusion.with_user(self.tech).unlink()
        # an exclusion between the values that make variants: the impossible variant is archived, not deleted
        with Form(red.with_user(self.tech)) as form:
            with form.exclude_for.new() as line:
                line.product_tmpl_id = product
                line.value_ids.add(s800)
        product.invalidate_recordset()
        self.assertEqual(len(product.with_context(active_test=False).product_variant_ids), 4, "nothing is deleted")
        self.assertEqual(len(product.product_variant_ids), 3, "the impossible variant is archived")
        # archive instead of delete
        center = env['mrp.workcenter'].create({'name': 'D-24 cutting', 'code': 'D24'})
        bom = env['mrp.bom'].create({'product_tmpl_id': product.id, 'operation_ids': [
            (0, 0, {'name': 'Cut', 'workcenter_id': center.id, 'time_cycle_manual': 10.0})]})
        for record in (bom.operation_ids, bom, center, product):
            record.action_archive()
            self.assertFalse(record.active, record._name)
            with self.assertRaises(AccessError):
                record.unlink()
        # the administrator deletes
        exclusion.with_user(self.env.ref('base.user_admin')).unlink()
        self.assertFalse(white.exclude_for)
