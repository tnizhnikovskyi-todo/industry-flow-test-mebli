import logging

_logger = logging.getLogger(__name__)

SHEET_L, SHEET_W = 2800, 2070
SHEETS = {'board_sonoma': 30, 'board_white': 30, 'board_anthr': 20, 'board_mdf': 20, 'board_hdf': 20}
EDGE_METRES = {'edge_sonoma_04': 900, 'edge_sonoma_2': 700, 'edge_white_04': 900, 'edge_white_2': 700,
               'edge_anthr_04': 700, 'edge_anthr_2': 600, 'edge_mdf_04': 700, 'edge_mdf_2': 800}
FITTINGS = {'fit_hinge': 20, 'fit_slide': 3, 'fit_guide': 20, 'fit_legs': 50}  # the slide system runs short on purpose
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


# price extras by product (the cost of a decor differs by the area it covers): template, attribute value -> UAH
EXTRAS = {
    ('prod_wardrobe', 'val_body_sonoma'): 1200, ('prod_wardrobe', 'val_body_anthr'): 600,
    ('prod_wardrobe', 'val_facade_mdf'): 2800,
    ('prod_dresser', 'val_body_sonoma'): 300, ('prod_dresser', 'val_body_anthr'): 250,
    ('prod_dresser', 'val_facade_mdf'): 800,
    ('prod_kitchen', 'val_body_sonoma'): 250, ('prod_kitchen', 'val_body_anthr'): 200,
    ('prod_kitchen', 'val_facade_mdf'): 600,
}


def _set_extras(env):
    for (template, value), extra in EXTRAS.items():
        tmpl, attribute_value = env.ref(f'td_mebli_demo.{template}'), env.ref(f'td_mebli_demo.{value}')
        tmpl.attribute_line_ids.product_template_value_ids.filtered(
            lambda ptav: ptav.product_attribute_value_id == attribute_value).price_extra = extra


# D-10 (AC-011): the standard exclusions of the configurator — «decor X: only edge X». The anthracite body of the
# wardrobe and the kitchen goes only with the 2 mm edge (no 0.4 mm). The exclusions are product data of the demo
# catalog (product.template.attribute.exclusion refers to the values of the product, which have no xmlid): the config
# package A-12 has no products; the templates of a customer get them on the product form (master data, A-13 / B-04).
EXCLUSIONS = [
    ('prod_wardrobe', 'val_body_anthr', ['val_edge_04']),
    ('prod_kitchen', 'val_body_anthr', ['val_edge_04']),
]


def _ptav(tmpl, value_xmlid):
    value = tmpl.env.ref(f'td_mebli_demo.{value_xmlid}')
    return tmpl.attribute_line_ids.product_template_value_ids.filtered(lambda v: v.product_attribute_value_id == value)


def _set_exclusions(env):
    for template, value, excluded in EXCLUSIONS:
        tmpl = env.ref(f'td_mebli_demo.{template}')
        ptav = _ptav(tmpl, value)
        others = sum((_ptav(tmpl, x) for x in excluded), env['product.template.attribute.value'])
        current = ptav.exclude_for.filtered(lambda e: e.product_tmpl_id == tmpl)
        if current:
            current.value_ids = [(6, 0, others.ids)]
        else:
            env['product.template.attribute.exclusion'].create({
                'product_tmpl_id': tmpl.id, 'product_template_attribute_value_id': ptav.id,
                'value_ids': [(6, 0, others.ids)]})


def _add_stock(env, location, product, quantity, lot=None):
    env['stock.quant'].with_context(inventory_mode=True).create({
        'product_id': product.id, 'location_id': location.id, 'lot_id': lot.id if lot else False,
        'inventory_quantity': quantity}).action_apply_inventory()


def post_init_hook(env):
    _set_company_currency(env)
    _set_extras(env)
    _set_exclusions(env)
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
            lot = Lot.create({'name': f'ОБР-{product.default_code}-{index}', 'product_id': product.id,
                              'td_length_mm': length, 'td_width_mm': width, 'td_is_offcut': True})
            _add_stock(env, location, product, lot.td_area_m2, lot)
    for xmlid, metres in {**EDGE_METRES, **FITTINGS}.items():
        if metres:
            _add_stock(env, location, env.ref(f'td_mebli_demo.{xmlid}'), metres)
