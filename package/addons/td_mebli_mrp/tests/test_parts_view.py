from odoo.tests import Form, tagged

from .common import TdMebliCommon


@tagged('post_install', '-at_install')
class TestPartsWhereTheShopWorks(TdMebliCommon):
    """Request of the owner: the parts of the order BoM are seen in the manufacturing order and in the work order of the
    tablet; the board and edge banding lines are marked as calculated from the parts. Read only, nothing new to enter."""

    def setUp(self):
        super().setUp()
        self.bom = self.env['mrp.bom']._td_generate_order_bom(self.cabinet, self.dims, self.selections)
        self.production = self.env['mrp.production'].create({
            'product_id': self.cabinet.id, 'product_qty': 1.0, 'bom_id': self.bom.id})
        self.production.action_confirm()

    def test_production_shows_the_parts_of_its_bom(self):
        production = self.production
        self.assertEqual(production.td_part_ids, self.bom.td_part_ids)
        self.assertEqual(production.td_part_count, self.bom.td_part_count)
        self.assertAlmostEqual(production.td_board_area_m2, self.bom.td_board_area_m2, places=4)
        self.assertAlmostEqual(production.td_edge_length_m, self.bom.td_edge_length_m, places=3)
        # two pieces: the parts are per piece, the totals are for the whole order
        production.product_qty = 2.0
        self.assertEqual(production.td_part_ids, self.bom.td_part_ids)
        self.assertEqual(production.td_part_count, 2 * self.bom.td_part_count)
        self.assertAlmostEqual(production.td_board_area_m2, 2 * self.bom.td_board_area_m2, places=4)
        self.assertAlmostEqual(production.td_edge_length_m, 2 * self.bom.td_edge_length_m, places=3)
        self.assertEqual(production.workorder_ids[:1].td_part_count, 2 * self.bom.td_part_count)
        # not stored: no new column, nothing to enter
        for name in ('td_part_ids', 'td_part_count', 'td_board_area_m2', 'td_edge_length_m'):
            field = production._fields[name]
            self.assertFalse(field.store, name)
            self.assertTrue(field.readonly, name)

    def test_production_without_parts(self):
        plain = self.env['mrp.bom'].create({
            'product_tmpl_id': self.fitting.product_tmpl_id.id, 'product_qty': 1.0,
            'bom_line_ids': [(0, 0, {'product_id': self.board_a.id, 'product_qty': 1.0})]})
        production = self.env['mrp.production'].create({
            'product_id': self.fitting.id, 'product_qty': 1.0, 'bom_id': plain.id})
        self.assertFalse(production.td_part_ids)
        self.assertEqual(production.td_part_count, 0)
        self.assertFalse(production.move_raw_ids.td_from_parts)
        self.assertFalse(plain.bom_line_ids.td_from_parts)

    def test_workorder_shows_the_parts_of_its_production(self):
        self.assertTrue(self.production.workorder_ids)
        for workorder in self.production.workorder_ids:
            self.assertEqual(workorder.td_part_ids, self.bom.td_part_ids)
            self.assertEqual(workorder.td_part_count, self.bom.td_part_count)
        self.assertFalse(self.env['mrp.workorder']._fields['td_part_ids'].store)
        action = self.production.workorder_ids[0].action_td_parts()
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['res_id'], self.production.workorder_ids[0].id)
        self.assertEqual(action['views'][0][0], self.env.ref('td_mebli_mrp.mrp_workorder_td_parts_form').id)

    def test_board_and_edge_lines_are_marked_from_parts(self):
        marked = self.bom.bom_line_ids.filtered('td_from_parts')
        self.assertEqual(set(marked.product_id.mapped('td_material_kind')), {'board', 'edge'})
        self.assertEqual(marked.product_id, self.bom.td_part_ids.material_id | self.bom.td_part_ids.edge_product_id)
        fitting_line = self.bom.bom_line_ids.filtered(lambda line: line.product_id == self.fitting)
        self.assertTrue(fitting_line)
        self.assertFalse(fitting_line.td_from_parts)
        self.assertFalse(self.env['mrp.bom.line']._fields['td_from_parts'].store)

    def test_component_moves_are_marked_from_parts(self):
        moves = self.production.move_raw_ids
        self.assertEqual(moves.filtered('td_from_parts').product_id,
                         self.bom.bom_line_ids.filtered('td_from_parts').product_id)
        self.assertFalse(moves.filtered(lambda move: move.product_id == self.fitting).td_from_parts)
        self.assertFalse(self.env['stock.move']._fields['td_from_parts'].store)

    def test_a_board_line_without_parts_of_that_board_is_not_marked(self):
        """A board added by hand that no part is cut from keeps its own quantity: not marked."""
        line = self.env['mrp.bom.line'].create({'bom_id': self.bom.id, 'product_id': self.board_b.id, 'product_qty': 2.0})
        self.assertFalse(line.td_from_parts)

    def test_a_quantity_that_differs_from_the_parts_is_not_marked(self):
        """Edited by hand or parts added later without recalculation: the mark does not claim what is not true."""
        board_line = self.bom.bom_line_ids.filtered(lambda line: line.product_id == self.board_a)
        self.assertTrue(board_line.td_from_parts)
        board_line.product_qty += 1.0
        self.assertFalse(board_line.td_from_parts)
        board_line.product_qty -= 1.0
        self.assertTrue(board_line.td_from_parts)
        self.env['td.mebli.part'].create({
            'bom_id': self.bom.id, 'name': 'Extra shelf', 'material_id': self.board_a.id,
            'qty': 1, 'length_mm': 500, 'width_mm': 400})
        self.assertFalse(board_line.td_from_parts)

    def test_views_load(self):
        """The new tab and the tablet dialog render with the fields of this module."""
        with Form(self.production) as form:
            self.assertEqual(len(form.td_part_ids), len(self.bom.td_part_ids))
        Form(self.production.workorder_ids[0], view='td_mebli_mrp.mrp_workorder_td_parts_form')
