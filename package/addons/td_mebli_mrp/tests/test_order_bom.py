from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TdMebliCommon


@tagged('post_install', '-at_install')
class TestOrderBom(TdMebliCommon):

    def _generate(self, dims=None, selections=None):
        return self.env['mrp.bom']._td_generate_order_bom(
            self.cabinet, dims or self.dims, selections or self.selections)

    def test_generate(self):
        bom = self._generate()
        self.assertTrue(bom.td_order_bom)
        self.assertEqual(bom.td_template_bom_id, self.template_bom)
        self.assertEqual(bom.td_part_count, 6)
        lines = {line.product_id: line.product_qty for line in bom.bom_line_ids}
        # body: 2 sides 0.7x0.5 + top 0.768x0.5 = 0.7+0.384 = 1.084 m2, +10 % waste
        self.assertAlmostEqual(lines[self.board_a], 1.084 * 1.1, places=2)
        # facade: 2 doors 0.696x0.396 = 0.551232 m2, +10 %
        self.assertAlmostEqual(lines[self.facade], 0.551232 * 1.1, places=2)
        self.assertAlmostEqual(lines[self.back], 0.79 * 0.69, places=2)
        # edge A: sides 2x0.7 + top 2x0.768, plus 3 edged sides... allowance 30 mm for every edged side
        edge_a = 2 * (0.7 + 0.03) + 2 * (0.768 + 0.03)
        self.assertAlmostEqual(lines[self.edge_a], edge_a, places=2)
        # edge on facade is 2 mm and exists only for the facade board
        edge_f = 2 * (2 * 0.696 + 2 * 0.396 + 4 * 0.03)
        self.assertAlmostEqual(lines[self.edge_f], edge_f, places=2)
        self.assertEqual(lines[self.fitting], 1.0)
        self.assertEqual(self.env.ref('uom.product_uom_square_meter'),
                         bom.bom_line_ids.filtered(lambda line: line.product_id == self.board_a).product_uom_id)
        operations = {op.name: op.time_cycle_manual for op in bom.operation_ids}
        self.assertEqual(operations, {'Cutting': 12.0, 'Assembly': 60.0})
        self.assertEqual(bom.td_width, 800)

    def test_generate_other_dims_changes_quantities(self):
        small = self._generate({'width': 400, 'height': 500, 'depth': 300})
        big = self._generate()
        qty = lambda bom: sum(bom.bom_line_ids.filtered(lambda l: l.product_id == self.board_a).mapped('product_qty'))
        self.assertLess(qty(small), qty(big))

    def test_out_of_range(self):
        with self.assertRaises(UserError):
            self._generate({'width': 3000, 'height': 700, 'depth': 500})

    def test_missing_edge(self):
        # board B has only 0.4 mm edge
        with self.assertRaises(UserError):
            self._generate(selections=self.val_b | self.val_f | self.val_e2)

    def test_bom_find_excludes_order_bom(self):
        bom = self._generate()
        found = self.env['mrp.bom']._bom_find(self.cabinet)[self.cabinet]
        self.assertEqual(found, self.template_bom)
        self.assertNotEqual(found, bom)

    def test_bom_cost(self):
        bom = self._generate()
        cost = self.cabinet._compute_bom_price(bom)
        materials = sum(
            line.product_id.standard_price * line.product_qty for line in bom.bom_line_ids)
        operations = 12.0 / 60 * 600.0 + 60.0 / 60 * 300.0
        self.assertAlmostEqual(cost, materials + operations, places=2)

    def _calendar(self, weekly_hours):
        return self.env['resource.calendar'].create({
            'name': f'Section {weekly_hours} h', 'attendance_ids': [(5, 0, 0)] + [
                (0, 0, {'name': f'Day {day}', 'dayofweek': str(day), 'hour_from': 8.0, 'hour_to': 8.0 + weekly_hours / 5.0,
                        'day_period': 'morning'}) for day in range(5)]})

    def test_capacity_from_calendar(self):
        """The weekly capacity is read from the working calendar of the section times its parallel capacity; nothing is entered."""
        field = self.env['mrp.workcenter']._fields['td_capacity_hours']
        self.assertTrue(field.compute and not field.store)
        self.wc_asm.resource_calendar_id = self._calendar(30)
        self.assertAlmostEqual(self.wc_asm.td_capacity_hours, 30.0, places=2)
        self.wc_asm.time_efficiency = 50.0  # the efficiency is in the expected duration, not in the capacity
        self.assertAlmostEqual(self.wc_asm.td_capacity_hours, 30.0, places=2)
        self.wc_asm.capacity_ids = [(0, 0, {'product_uom_id': self.env.ref('uom.product_uom_unit').id, 'capacity': 2.0})]
        self.assertAlmostEqual(self.wc_asm.td_capacity_hours, 60.0, places=2)

    def test_workorder_load(self):
        """The load of a section is the sum of its operations in percent of the weekly capacity of its calendar."""
        self.wc_asm.resource_calendar_id = self._calendar(40)
        production = self.env['mrp.production'].create({
            'product_id': self.cabinet.id, 'product_qty': 1.0, 'bom_id': self._generate().id})
        production.action_confirm()
        workorder = production.workorder_ids.filtered(lambda wo: wo.workcenter_id == self.wc_asm)
        self.assertAlmostEqual(workorder.td_expected_hours, workorder.duration_expected / 60.0, places=2)
        self.assertAlmostEqual(workorder.td_load_pct, workorder.td_expected_hours / 40.0 * 100.0, places=2)
        self.assertTrue(workorder.td_load_stage)
        self.assertEqual(workorder.td_load_zone, 'within')
        self.assertAlmostEqual(self.wc_asm.workcenter_load, workorder.duration_expected, places=2)
        # a section that has less than one operation needs in a week is over its capacity
        self.wc_asm.resource_calendar_id = self._calendar(0.5)
        self.assertEqual(workorder.td_load_zone, 'over')
        self.assertAlmostEqual(workorder.td_load_pct, workorder.td_expected_hours / 0.5 * 100.0, places=2)

    def test_bought_facade_is_not_cut(self):
        """Ready-made fronts bought by a template line for the chosen facade value: no facade part under cutting
        (no double counting); another facade value still cuts the doors from board."""
        fronts = self.env['product.product'].create({
            'name': 'Painted fronts', 'type': 'consu', 'standard_price': 900.0, 'td_material_kind': 'facade'})
        val_g = self.env['product.attribute.value'].create({
            'name': 'G', 'attribute_id': self.attr_facade.id, 'td_component_product_id': self.board_a.id})
        self.cabinet_tmpl.attribute_line_ids = [
            (0, 0, {'attribute_id': self.attr_facade.id, 'value_ids': [(6, 0, (self.val_f | val_g).ids)]})]
        ptav_f = self.cabinet_tmpl.attribute_line_ids.product_template_value_ids.filtered(
            lambda v: v.product_attribute_value_id == self.val_f)
        self.template_bom.bom_line_ids = [(0, 0, {
            'product_id': fronts.id, 'product_qty': 2.0, 'bom_product_template_attribute_value_ids': [(6, 0, ptav_f.ids)]})]
        bom = self._generate()
        self.assertFalse(bom.td_part_ids.filtered(lambda part: part.name == 'Door'))
        self.assertEqual(bom.td_part_count, 4)
        products = bom.bom_line_ids.product_id
        self.assertIn(fronts, products)
        self.assertNotIn(self.facade, products)
        self.assertNotIn(self.edge_f, products)
        other = self._generate(selections=self.val_a | val_g | self.val_e04 | self.val_fit)
        self.assertNotIn(fronts, other.bom_line_ids.product_id, "the line applies to the painted facade value only")
        self.assertTrue(other.td_part_ids.filtered(lambda part: part.name == 'Door'))

    def test_custom_size_name(self):
        """A typed size reads 'Width, mm: 1800' (the placeholder value name is not shown)."""
        attribute = self.env['product.attribute'].create({
            'name': 'Width, mm', 'create_variant': 'no_variant', 'td_dimension': 'width',
            'value_ids': [(0, 0, {'name': 'Enter size', 'is_custom': True})]})
        value = attribute.value_ids[:1]
        tmpl = self.env['product.template'].create({
            'name': 'Dim test', 'attribute_line_ids': [(0, 0, {'attribute_id': attribute.id, 'value_ids': [(6, 0, value.ids)]})]})
        ptav = tmpl.attribute_line_ids.product_template_value_ids[:1]
        custom = self.env['product.attribute.custom.value'].create({
            'custom_product_template_attribute_value_id': ptav.id, 'custom_value': '1800'})
        self.assertEqual(custom.name, f'{attribute.name}: 1800')

    def test_static_board_and_edge_of_the_template_are_not_counted_twice(self):
        """CHECKS.md No. 28 (AC-013): the template has static lines of the white board and its edge banding (as a
        standard bill of materials would). The order specification takes board and edge banding from the parts only:
        for decor B there is no board A / edge A, for decor A the quantity is the one of the parts. Other lines of the
        template (a back panel board without a part rule, a fitting) are copied."""
        panel = self.env['product.product'].create({
            'name': 'Plinth board', 'type': 'consu', 'td_material_kind': 'board',
            'uom_id': self.env.ref('uom.product_uom_square_meter').id})
        self.cabinet_tmpl.attribute_line_ids = [
            (0, 0, {'attribute_id': self.attr_body.id, 'value_ids': [(6, 0, (self.val_a | self.val_b).ids)]})]
        self.template_bom.bom_line_ids = [
            (0, 0, {'product_id': self.board_a.id, 'product_qty': 6.5}),
            (0, 0, {'product_id': self.edge_a.id, 'product_qty': 22.0}),
            (0, 0, {'product_id': panel.id, 'product_qty': 0.3}),
            (0, 0, {'product_id': self.fitting.id, 'product_qty': 4.0}),
        ]
        bom_b = self._generate(selections=self.val_b | self.val_f | self.val_e04 | self.val_fit)
        lines_b = bom_b.bom_line_ids
        self.assertNotIn(self.board_a, lines_b.product_id, "decor B must not need the white board of the template")
        self.assertNotIn(self.edge_a, lines_b.product_id)
        self.assertAlmostEqual(sum(lines_b.filtered(lambda l: l.product_id == self.board_b).mapped('product_qty')),
                               1.084 * 1.1, places=2)
        self.assertEqual(len(lines_b.filtered(lambda l: l.product_id == self.board_b)), 1)
        self.assertIn(panel, lines_b.product_id)
        self.assertEqual(sum(lines_b.filtered(lambda l: l.product_id == self.fitting).mapped('product_qty')), 5.0)
        bom_a = self._generate()
        board_lines = bom_a.bom_line_ids.filtered(lambda l: l.product_id == self.board_a)
        self.assertEqual(len(board_lines), 1)
        self.assertAlmostEqual(board_lines.product_qty, 1.084 * 1.1, places=2)
        edge_lines = bom_a.bom_line_ids.filtered(lambda l: l.product_id == self.edge_a)
        self.assertEqual(len(edge_lines), 1)
        self.assertAlmostEqual(edge_lines.product_qty, 2 * (0.7 + 0.03) + 2 * (0.768 + 0.03), places=2)
        self.assertTrue(all(bom_a.bom_line_ids.filtered(
            lambda l: l.product_id.td_material_kind in ('board', 'edge') and l.product_id != panel).mapped('td_from_parts')))
