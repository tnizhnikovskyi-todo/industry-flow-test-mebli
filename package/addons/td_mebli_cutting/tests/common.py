from odoo.addons.td_mebli_mrp.tests.common import TdMebliCommon


class TdMebliCuttingCommon(TdMebliCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        for board in (cls.board_a, cls.facade, cls.back):
            board.tracking = 'lot'
            board.td_sheet_length_mm = 2800
            board.td_sheet_width_mm = 2070
        cls.board_a.default_code = 'A'
        cls.warehouse = env['stock.warehouse'].search([('company_id', '=', env.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.sheet_lots = cls._add_lots(cls.board_a, 3)
        cls.facade_lots = cls._add_lots(cls.facade, 2)
        cls.back_lots = cls._add_lots(cls.back, 2)
        # box B function «business offcuts» (VP-02): on for the fixtures, a test of box A switches it off
        cls._feature('offcut')

    @classmethod
    def _feature(cls, name, on=True, user=None):
        group = cls.env.ref(f'td_mebli_base.group_feature_{name}')
        (user or cls.env.user).write({'group_ids': [(4 if on else 3, group.id)]})

    @classmethod
    def _add_lots(cls, product, count, length=2800, width=2070, offcut=False, prefix='SHEET'):
        lots = cls.env['stock.lot']
        for index in range(count):
            lot = cls.env['stock.lot'].create({
                'name': f'{prefix}-{product.id}-{index}', 'product_id': product.id,
                'td_length_mm': length, 'td_width_mm': width, 'td_is_offcut': offcut})
            cls.env['stock.quant'].with_context(inventory_mode=True).create({
                'product_id': product.id, 'location_id': cls.stock_location.id, 'lot_id': lot.id,
                'inventory_quantity': length * width / 1_000_000.0}).action_apply_inventory()
            lots |= lot
        return lots

    @classmethod
    def _make_production(cls, dims=None):
        bom = cls.env['mrp.bom']._td_generate_order_bom(cls.cabinet, dims or cls.dims, cls.selections)
        production = cls.env['mrp.production'].create({
            'product_id': cls.cabinet.id, 'product_qty': 1.0, 'bom_id': bom.id,
            'product_uom_id': cls.cabinet.uom_id.id})
        production.action_confirm()
        return production
