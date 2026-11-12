"""Promised and forecast dates of the demo order book; made-to-order items bought by the standard (S-02, F-23, F-31, NG-01).

seed_dates(env, people, partners, rnd) runs at the end of seed_showcase. The made-to-order items (painted fronts, a quartz
worktop, a sliding-door profile) are products with the routes «Replenish on Order (MTO)» and «Buy» and a vendor pricelist
line (product.supplierinfo); they are components of the kitchen and wardrobe bills of materials. The order of the sales
demo (SALES §6, scene 4) is confirmed: the standard creates the manufacturing orders and, for the components, the purchase
orders. The buyer then works in Purchase only: confirms the orders, enters the date the paint shop moved (date_planned)
and receives the profile. The sales order shows it read only. Everything is fictional.
"""
from datetime import timedelta

from odoo import fields

from .scenario import _custom

# name, city: fictional suppliers of made-to-order items; phones of the format +380 00 000 00 NN
SUPPLIERS = [
    ('Фарбоцех «Палітра»', 'Біла Церква'), ('Камінь-Майстер', 'Житомир'), ('Профіль-Систем', 'Київ'),
]

# key, name, unit xmlid, cost (UAH; painted front of a 600 module ~0.43 m2 — the planned margin of the show order stays ~20 %), supplier index, supplier lead time (days), template BoM, quantity per unit,
# material kind (td_mebli_mrp), facade value the line applies to (standard «Apply on Variants» of the BoM line; None = always)
# The painted fronts are ready-made facades: for the facade «МДФ Білий матовий» the kitchen buys them and the part rule
# «Фасад» is not cut from board (td_mebli_mrp: no double counting of the facades).
COMPONENTS = [
    ('fronts_9010', 'Фасади МДФ фарбовані, RAL 9010 мат', 'uom.product_uom_unit', 1100.0, 0, 14, 'prod_kitchen', 1.0,
     'facade', 'val_facade_mdf'),
    ('worktop_quartz', 'Стільниця кварцова 38 мм', 'uom.product_uom_meter', 1600.0, 1, 10, 'prod_kitchen', 0.6, False, None),
    ('profile_champagne', 'Профіль шафи-купе, алюміній шампань', 'uom.product_uom_unit', 2400.0, 2, 5, 'prod_wardrobe', 1.0,
     False, None),
]

# standard manufacturing lead time of the template bills of materials (mrp.bom.produce_delay), days
PRODUCE_DELAY = {'prod_kitchen': 12, 'prod_wardrobe': 12}


def _suppliers(env):
    Partner = env['res.partner']
    found = Partner
    for index, (name, city) in enumerate(SUPPLIERS):
        found |= Partner.create({
            'name': name, 'company_type': 'company', 'city': city, 'country_id': env.ref('base.ua').id,
            'phone': f'+380 00 000 00 {60 + index:02d}', 'email': f'orders{index + 1}@supplier-demo.example',
            'lang': 'uk_UA', 'supplier_rank': 1,
        })
    return found


def _components(env, suppliers):
    """Made-to-order items as standard products: MTO + Buy, the supplier and his lead time in the vendor pricelist,
    a line of the template bill of materials. From now on every kitchen and wardrobe order buys them on confirmation."""
    routes = [env.ref('stock.route_warehouse0_mto').id, env.ref('purchase_stock.route_warehouse0_buy').id]
    found = {}
    for key, name, uom, cost, supplier, delay, template, qty, kind, applies_to in COMPONENTS:
        product = env['product.product'].create({
            'name': name, 'type': 'consu', 'is_storable': True, 'uom_id': env.ref(uom).id,
            'standard_price': cost, 'purchase_ok': True, 'sale_ok': False, 'route_ids': [(6, 0, routes)],
            'td_material_kind': kind,
            'seller_ids': [(0, 0, {'partner_id': suppliers[supplier].id, 'price': cost, 'delay': delay})],
        })
        tmpl = env.ref(f'td_mebli_demo.{template}')
        bom = env['mrp.bom']._bom_find(tmpl.product_variant_id)[tmpl.product_variant_id]
        ptavs = tmpl.attribute_line_ids.product_template_value_ids.filtered(
            lambda v: applies_to and v.product_attribute_value_id == env.ref(f'td_mebli_demo.{applies_to}'))
        bom.write({'bom_line_ids': [(0, 0, {'product_id': product.id, 'product_qty': qty, 'product_uom_id': product.uom_id.id,
                                            'bom_product_template_attribute_value_ids': [(6, 0, ptavs.ids)]})]})
        found[key] = product
    for template, days in PRODUCE_DELAY.items():
        variant = env.ref(f'td_mebli_demo.{template}').product_variant_id
        env['mrp.bom']._bom_find(variant)[variant].produce_delay = days
    return found


def _line(env, product_xmlid, dims, body, facade, edge, fitting, qty):
    tmpl = env.ref(f'td_mebli_demo.{product_xmlid}')
    chosen = tmpl.attribute_line_ids.product_template_value_ids.filtered(
        lambda v: v.product_attribute_value_id in [env.ref(f'td_mebli_demo.{x}') for x in (body, facade, edge, fitting)])
    width, height, depth = dims
    return (0, 0, {
        'product_id': tmpl.product_variant_id.id, 'product_uom_qty': qty,
        'product_custom_attribute_value_ids': [
            _custom(env, tmpl, 'w', width), _custom(env, tmpl, 'h', height), _custom(env, tmpl, 'd', depth)],
        'product_no_variant_attribute_value_ids': [(6, 0, chosen.ids)],
    })


def _book(env, rnd):
    """Promised dates of the existing order book: most orders keep the date; one open order is late because of the
    workshop (the reason «Company»)."""
    orders = env['sale.order'].search([('state', '=', 'sale')], order='date_order')
    for order in orders:
        shop = order._td_shop_date()
        ordered = fields.Date.context_today(order, order.date_order)
        promised = max(shop + timedelta(days=rnd.randint(2, 6)), ordered + timedelta(days=rnd.randint(21, 30)))
        order.commitment_date = fields.Datetime.to_datetime(promised) + timedelta(hours=15)
    late = orders.filtered(lambda o: o.td_stage == 'progress')
    if late:
        first = late[0]
        first.commitment_date = fields.Datetime.to_datetime(first._td_shop_date() - timedelta(days=3)) + timedelta(hours=15)


def _receive(picking):
    for move in picking.move_ids:
        move.quantity = move.product_uom_qty
        move.picked = True
    picking.with_context(skip_backorder=True, skip_sms=True).button_validate()


def _show_order(env, people, partners, components):
    """The order of the demo: a kitchen and a sliding wardrobe in one contract; the painted fronts are late."""
    salon = people['salon']
    store = people['store']
    now = fields.Datetime.now()
    order = env['sale.order'].create({
        'partner_id': partners[1].id,
        'order_line': [
            _line(env, 'prod_kitchen', (600, 720, 560), 'val_body_white', 'val_facade_mdf', 'val_edge_2', 'val_fit_premium', 9.0),
            _line(env, 'prod_wardrobe', (1800, 2400, 600), 'val_body_white', 'val_facade_mdf', 'val_edge_2', 'val_fit_premium', 1.0),
        ],
    })
    ordered = now - timedelta(days=6, hours=3)
    order.write({'user_id': salon.id, 'date_order': ordered, 'client_order_ref': 'Кухня й шафа-купе, квартира',
                 'payment_term_id': partners[1].property_payment_term_id.id,
                 'note': 'Термін виготовлення — 28 днів від дня передоплати. Гарантія на виріб — 24 місяці. '
                         'Доставка й монтаж — за графіком монтажів.'})
    order = order.with_user(salon)
    order.order_line.action_td_generate_bom()
    # the standard: MTO -> manufacturing orders for the products, MTO + Buy -> requests for quotation for the components
    order.action_confirm()
    order = order.with_env(env)
    order.date_order = ordered
    # the workshop starts in four days (after the prepayment); the end follows from the lead time of the BoM (12 days)
    order.mrp_production_ids.write({'date_start': now + timedelta(days=4)})
    promised = fields.Date.context_today(order, ordered) + timedelta(days=28)
    order.commitment_date = fields.Datetime.to_datetime(promised) + timedelta(hours=15)
    # the buyer works in Purchase: confirms the requests, enters the supplier dates, receives what came
    purchases = order._get_purchase_orders()
    dates = {
        # the paint shop moved the fronts two days past the promise: + 12 days of the workshop = two weeks of shift
        components['fronts_9010']: fields.Datetime.to_datetime(promised + timedelta(days=2)) + timedelta(hours=10),
        components['worktop_quartz']: now + timedelta(days=3),
        components['profile_champagne']: now - timedelta(days=1, hours=2),
    }
    for purchase in purchases:
        purchase.write({'user_id': store.id})
        purchase.button_confirm()
        purchase.write({'date_order': ordered + timedelta(hours=26), 'date_approve': ordered + timedelta(hours=26)})
        for line in purchase.order_line:
            if line.product_id in dates:
                line.date_planned = dates[line.product_id]
    profile = purchases.order_line.filtered(lambda line: line.product_id == components['profile_champagne']).order_id
    for picking in profile.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')):
        _receive(picking)
    return order


def seed_dates(env, people, partners, rnd):
    from .showcase import _note
    # the system bot writes the tracking messages in the chatter: a Ukrainian name, no Latin in the frame
    env.ref('base.partner_root').name = 'Система'
    suppliers = _suppliers(env)
    _book(env, rnd)
    components = _components(env, suppliers)
    order = _show_order(env, people, partners, components)
    fronts = order._get_purchase_orders().order_line.filtered(lambda line: line.product_id == components['fronts_9010'])
    moved = fields.Date.context_today(fronts, fronts.date_planned)
    _note(order, people['salon'], 'Клієнт погодив кухню й шафу-купе в одному договорі, фасади — фарбовані RAL 9010 мат.',
          order.date_order + timedelta(hours=2))
    _note(fronts.order_id, people['store'], f'Фарбоцех «Палітра» переніс фасади на {moved.strftime("%d.%m.%Y")}: черга на фарбування.',
          fields.Datetime.now() - timedelta(hours=3))
    _note(order, people['store'], f'Фарбоцех «Палітра» переніс фасади на {moved.strftime("%d.%m.%Y")} (закупівля {fronts.order_id.name}).',
          fields.Datetime.now() - timedelta(hours=2))
    return order
