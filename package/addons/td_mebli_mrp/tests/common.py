from odoo.tests import TransactionCase


class TdMebliCommon(TransactionCase):
    """Own fixtures: the tests do not depend on td_mebli_demo."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        uom_m2 = env.ref('uom.product_uom_square_meter')
        uom_m = env.ref('uom.product_uom_meter')
        Product = env['product.product']

        def material(name, kind, uom, price, **extra):
            return Product.create({
                'name': name, 'type': 'consu', 'is_storable': True, 'uom_id': uom.id,
                'standard_price': price, 'td_material_kind': kind, **extra})

        cls.board_a = material('Board A', 'board', uom_m2, 100.0, td_waste_pct=10.0,
                               td_sheet_length_mm=2800, td_sheet_width_mm=2070, td_thickness_mm=16)
        cls.board_b = material('Board B', 'board', uom_m2, 200.0, td_waste_pct=10.0)
        cls.facade = material('Facade MDF', 'board', uom_m2, 300.0, td_waste_pct=10.0)
        cls.back = material('Back HDF', 'board', uom_m2, 40.0, td_waste_pct=0.0)
        cls.edge_a = material('Edge A 0.4', 'edge', uom_m, 10.0, td_matches_board_id=cls.board_a.id, td_edge_thickness=0.4)
        cls.edge_a2 = material('Edge A 2', 'edge', uom_m, 20.0, td_matches_board_id=cls.board_a.id, td_edge_thickness=2.0)
        cls.edge_b = material('Edge B 0.4', 'edge', uom_m, 12.0, td_matches_board_id=cls.board_b.id, td_edge_thickness=0.4)
        cls.edge_f = material('Edge F 2', 'edge', uom_m, 25.0, td_matches_board_id=cls.facade.id, td_edge_thickness=2.0)
        cls.fitting = material('Fitting set', 'fitting', env.ref('uom.product_uom_unit'), 500.0)

        def attribute(name, role=None, dimension=None, values=()):
            attr = env['product.attribute'].create({
                'name': name, 'create_variant': 'no_variant',
                'td_component_role': role, 'td_dimension': dimension,
                'value_ids': [(0, 0, vals) for vals in values],
            })
            return attr, attr.value_ids

        cls.attr_body, (cls.val_a, cls.val_b) = attribute('Body decor', 'body_board', values=[
            {'name': 'A', 'td_component_product_id': cls.board_a.id},
            {'name': 'B', 'td_component_product_id': cls.board_b.id}])
        cls.attr_facade, (cls.val_f,) = attribute('Facade decor', 'facade_board', values=[
            {'name': 'F', 'td_component_product_id': cls.facade.id}])
        cls.attr_edge, (cls.val_e04, cls.val_e2) = attribute('Edge', 'edge', values=[
            {'name': '0.4', 'td_edge_thickness': 0.4}, {'name': '2', 'td_edge_thickness': 2.0}])
        cls.attr_fit, (cls.val_fit,) = attribute('Fittings', 'fitting_set', values=[
            {'name': 'Std', 'td_component_product_id': cls.fitting.id}])

        cls.wc_cut = env['mrp.workcenter'].create({'name': 'Cut', 'costs_hour': 600.0})
        cls.wc_asm = env['mrp.workcenter'].create({'name': 'Assembly', 'costs_hour': 300.0})
        cls.cabinet = Product.create({
            'name': 'Cabinet', 'type': 'consu', 'is_storable': True, 'list_price': 1000.0,
            'td_is_parametric': True,
            'td_width_nominal': 800, 'td_width_min': 400, 'td_width_max': 1200,
            'td_height_nominal': 700, 'td_height_min': 500, 'td_height_max': 900,
            'td_depth_nominal': 500, 'td_depth_min': 300, 'td_depth_max': 600,
            'td_edge_allowance_mm': 30,
            'td_part_rule_ids': [
                # side: depth x height, 2 pcs, long side edged
                (0, 0, {'name': 'Side', 'qty': 2, 'material_role': 'body_board',
                        'len_h': 1.0, 'wid_d': 1.0, 'edge_long_sides': 1}),
                # top: width - 32 x depth, 1 pc, both long sides edged
                (0, 0, {'name': 'Top', 'qty': 1, 'material_role': 'body_board',
                        'len_w': 1.0, 'len_const': -32.0, 'wid_d': 1.0, 'edge_long_sides': 2}),
                (0, 0, {'name': 'Door', 'qty': 2, 'material_role': 'facade_board',
                        'len_h': 1.0, 'len_const': -4.0, 'wid_w': 0.5, 'wid_const': -4.0,
                        'edge_long_sides': 2, 'edge_short_sides': 2}),
                (0, 0, {'name': 'Back', 'qty': 1, 'material_role': 'fixed', 'fixed_material_id': cls.back.id,
                        'len_h': 1.0, 'len_const': -10.0, 'wid_w': 1.0, 'wid_const': -10.0}),
            ],
        })
        cls.cabinet_tmpl = cls.cabinet.product_tmpl_id
        cls.template_bom = env['mrp.bom'].create({
            'product_tmpl_id': cls.cabinet_tmpl.id, 'product_qty': 1.0,
            'operation_ids': [
                (0, 0, {'name': 'Cutting', 'workcenter_id': cls.wc_cut.id, 'td_time_basis': 'per_part',
                        'td_time_rate': 2.0}),
                (0, 0, {'name': 'Assembly', 'workcenter_id': cls.wc_asm.id, 'time_cycle_manual': 60.0}),
            ],
        })
        cls.dims = {'width': 800, 'height': 700, 'depth': 500}
        cls.selections = cls.val_a | cls.val_f | cls.val_e04 | cls.val_fit
