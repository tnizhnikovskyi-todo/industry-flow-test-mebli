"""Promised and forecast dates of the demo order book, made-to-order items (S-02, F-23, F-31, NG-01).

seed_dates(env, people, partners, rnd) runs at the end of seed_showcase: it sets the promised date of every order,
adds made-to-order items (painted fronts, stone worktops, glass, sliding-door profiles) from fictional suppliers and
creates the order of the sales demo (SALES §6, scene 4): a kitchen and a wardrobe in one contract, where the painted
fronts come two weeks late and move the forecast date past the promised one. Everything is fictional.
"""
from datetime import timedelta

from odoo import fields

from .scenario import _custom

# name, city: fictional suppliers of made-to-order items; phones of the format +380 00 000 00 NN
SUPPLIERS = [
    ('Фарбоцех «Палітра»', 'Біла Церква'), ('Камінь-Майстер', 'Житомир'),
    ('Профіль-Систем', 'Київ'), ('Скло-Лайн', 'Вінниця'),
]

# item, supplier index, kind of product it goes with
ITEMS = {
    'prod_kitchen': [('Фасади МДФ фарбовані, RAL 9010 мат', 0), ('Стільниця кварцова 38 мм', 1), ('Скло для вітрини, загартоване', 3)],
    'prod_wardrobe': [('Профіль шафи-купе, алюміній шампань', 2), ('Дзеркало для дверей купе', 3)],
    'prod_dresser': [('Фасади МДФ фарбовані, RAL 7044 мат', 0)],
}

STATES = ['to_order', 'ordered', 'confirmed', 'confirmed', 'received']


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


def _today(env):
    return fields.Date.context_today(env.user)


def _book(env, suppliers, rnd):
    """Promised dates and made-to-order items of the existing order book: most orders keep the date."""
    today = _today(env)
    orders = env['sale.order'].search([('state', '=', 'sale')], order='date_order')
    for order in orders:
        shop = order._td_shop_date()
        ordered = fields.Date.context_today(order, order.date_order)
        kind = order.order_line[:1].product_id.product_tmpl_id
        key = next((k for k in ITEMS if env.ref(f'td_mebli_demo.{k}') == kind), None)
        open_order = order.td_stage in ('confirmed', 'progress')
        promised = max(shop + timedelta(days=rnd.randint(2, 6)), ordered + timedelta(days=rnd.randint(21, 30)))
        if open_order and key and rnd.random() < 0.6:
            for position, (name, supplier) in enumerate(ITEMS[key][:rnd.randint(1, len(ITEMS[key]))]):
                earliest = max(today + timedelta(days=rnd.randint(1, 12)), ordered + timedelta(days=7))
                arrive = min(promised - timedelta(days=rnd.randint(4, 9)), earliest)
                env['td.mebli.order.item'].create({
                    'order_id': order.id, 'sequence': position, 'name': name, 'supplier_id': suppliers[supplier].id,
                    'date_supplier': arrive, 'lead_days': rnd.choice([1, 2, 2, 3]),
                    'state': 'received' if arrive < today else rnd.choice(STATES[1:4]),
                })
        order.commitment_date = fields.Datetime.to_datetime(promised) + timedelta(hours=15)
    # two open orders do not make it: one because of the workshop (the reason «Company»), one because of a supplier
    late = orders.filtered(lambda o: o.td_stage == 'progress')
    if late:
        first = late[0]
        first.commitment_date = fields.Datetime.to_datetime(first._td_shop_date() - timedelta(days=3)) + timedelta(hours=15)
    if len(late) > 2:
        second = late[2]
        promised = fields.Date.context_today(second, second.commitment_date)
        env['td.mebli.order.item'].create({
            'order_id': second.id, 'sequence': 9, 'name': 'Стільниця кварцова 38 мм', 'supplier_id': suppliers[1].id,
            'date_supplier': promised + timedelta(days=4), 'lead_days': 2, 'state': 'confirmed'})


def _show_order(env, people, partners, suppliers):
    """The order of the demo: a kitchen and a sliding wardrobe in one contract; the painted fronts are late."""
    salon = people['salon']
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
    order.action_confirm()
    order = order.with_env(env)
    order.date_order = ordered
    # the workshop needs 12 days for this order (standard lead time of the BoM, set after the confirmation regenerated the
    # order BoM): the manufacturing orders end well before the promise
    order.order_line.td_bom_id.write({'produce_delay': 12})
    # the workshop starts in four days (after the prepayment); the end follows from the lead time of the BoM
    order.mrp_production_ids.write({'date_start': now + timedelta(days=4)})
    promised = fields.Date.context_today(order, ordered) + timedelta(days=28)
    order.commitment_date = fields.Datetime.to_datetime(promised) + timedelta(hours=15)
    Item = env['td.mebli.order.item']
    Item.create([
        {'order_id': order.id, 'sequence': 1, 'name': 'Фасади МДФ фарбовані, RAL 9010 мат', 'supplier_id': suppliers[0].id,
         'date_supplier': promised + timedelta(days=11), 'lead_days': 3, 'state': 'confirmed'},
        {'order_id': order.id, 'sequence': 2, 'name': 'Стільниця кварцова 38 мм', 'supplier_id': suppliers[1].id,
         'date_supplier': promised - timedelta(days=8), 'lead_days': 2, 'state': 'ordered'},
        {'order_id': order.id, 'sequence': 3, 'name': 'Профіль шафи-купе, алюміній шампань', 'supplier_id': suppliers[2].id,
         'date_supplier': _today(env) - timedelta(days=1), 'lead_days': 1, 'state': 'received'},
    ])
    return order


def seed_dates(env, people, partners, rnd):
    from .showcase import _note
    # the system bot writes the tracking messages in the chatter: a Ukrainian name, no Latin in the frame
    env.ref('base.partner_root').name = 'Система'
    suppliers = _suppliers(env)
    _book(env, suppliers, rnd)
    order = _show_order(env, people, partners, suppliers)
    fronts = order.td_item_ids.sorted('sequence')[:1]
    _note(order, people['salon'], 'Клієнт погодив кухню й шафу-купе в одному договорі, фасади — фарбовані RAL 9010 мат.',
          order.date_order + timedelta(hours=2))
    _note(order, people['store'], f'Фарбоцех «Палітра» переніс фасади на {fronts.date_supplier.strftime("%d.%m.%Y")}: черга на фарбування.',
          fields.Datetime.now() - timedelta(hours=2))
    return order
