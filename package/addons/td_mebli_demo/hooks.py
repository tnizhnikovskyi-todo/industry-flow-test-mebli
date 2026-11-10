import logging

_logger = logging.getLogger(__name__)

SHEET_L, SHEET_W = 2800, 2070
SHEETS = {'board_sonoma': 10, 'board_white': 8, 'board_anthr': 6, 'board_mdf': 6, 'board_hdf': 6}
EDGE_METRES = {'edge_sonoma_04': 500, 'edge_sonoma_2': 300, 'edge_white_04': 500, 'edge_white_2': 300,
               'edge_anthr_04': 400, 'edge_anthr_2': 300, 'edge_mdf_04': 400, 'edge_mdf_2': 300}
FITTINGS = {'fit_hinge': 20, 'fit_slide': 0, 'fit_guide': 20, 'fit_legs': 50}  # the slide system is out of stock
OFFCUTS = {'board_sonoma': [(1200, 700), (900, 450)]}


def _set_company_currency(env):
    """UAH as the company currency, only while there are no journal entries."""
    uah = env.ref('base.UAH')
    company = env.company
    if company.currency_id == uah:
        return
    if 'account.move' in env and env['account.move'].search_count([('company_id', '=', company.id)], limit=1):
        _logger.info('td_mebli_demo: company already has journal entries, currency is not changed')
        return
    uah.active = True
    company.currency_id = uah
    # price lists are created in the old currency; without this the sales screens would show dollars
    env['product.pricelist'].search([('company_id', 'in', [company.id, False])]).write({'currency_id': uah.id})


def _add_stock(env, location, product, quantity, lot=None):
    env['stock.quant'].with_context(inventory_mode=True).create({
        'product_id': product.id, 'location_id': location.id, 'lot_id': lot.id if lot else False,
        'inventory_quantity': quantity}).action_apply_inventory()


def post_init_hook(env):
    _set_company_currency(env)
    # a show database: no onboarding tours that click through the screens on their own
    env['res.users'].with_context(active_test=False).search([]).write({'tour_enabled': False})
    warehouse = env['stock.warehouse'].search([('company_id', '=', env.company.id)], limit=1)
    location = warehouse.lot_stock_id
    Lot = env['stock.lot']
    if Lot.search_count([('product_id', '=', env.ref('td_mebli_demo.board_sonoma').id)], limit=1):
        return
    for xmlid, count in SHEETS.items():
        product = env.ref(f'td_mebli_demo.{xmlid}')
        for index in range(1, count + 1):
            lot = Lot.create({'name': f'{product.default_code}-{index:03d}', 'product_id': product.id,
                              'td_length_mm': SHEET_L, 'td_width_mm': SHEET_W})
            _add_stock(env, location, product, lot.td_area_m2, lot)
    for xmlid, sizes in OFFCUTS.items():
        product = env.ref(f'td_mebli_demo.{xmlid}')
        for index, (length, width) in enumerate(sizes, start=1):
            lot = Lot.create({'name': f'OFF-{product.default_code}-{index}', 'product_id': product.id,
                              'td_length_mm': length, 'td_width_mm': width, 'td_is_offcut': True})
            _add_stock(env, location, product, lot.td_area_m2, lot)
    for xmlid, metres in {**EDGE_METRES, **FITTINGS}.items():
        if metres:
            _add_stock(env, location, env.ref(f'td_mebli_demo.{xmlid}'), metres)
