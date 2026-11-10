"""Showcase data of the demo factory: branding, role users, a living order book.

seed_showcase(env) runs once on a database that already has td_mebli_demo (catalog, stock). It is used for the
sales demo (docs/industries/mebli/prototype-real/): 22 orders in different stages, invoices and prepayments,
manufacturing orders with work orders in progress, finished cutting jobs with business offcuts, chatter history
written by different roles. Everything is fictional: company, people, customers, addresses and phones.
It uses only public ORM methods of the packages.
"""
import base64
import random
from datetime import timedelta

from odoo import fields
from odoo.tools import file_open

from .scenario import make_order

IMG = 'td_mebli_demo/static/img/'

COMPANY = {
    'name': 'Меблева фабрика «Демо»', 'street': 'вул. Заводська, 12', 'city': 'Київ', 'zip': '02000',
    'phone': '+380 44 555 01 00', 'email': 'office@demo-fabryka.example', 'website': 'https://demo-fabryka.example',
    'primary_color': '#3d2b1f', 'secondary_color': '#c9a06a',
}

# login, name, job, avatar, groups (xmlids)
USERS = [
    ('salon', 'Олена Мартинюк', 'Менеджер салону', 'avatar_salon', ['sales_team.group_sale_salesman']),
    ('salon2', 'Роман Лисенко', 'Менеджер салону', 'avatar_salon2', ['sales_team.group_sale_salesman']),
    ('salon3', 'Світлана Прокопенко', 'Менеджер салону', 'avatar_salon3', ['sales_team.group_sale_salesman']),
    ('tech', 'Андрій Ковальчук', 'Технолог-конструктор', 'avatar_tech',
     ['mrp.group_mrp_user', 'sales_team.group_sale_salesman_all_leads', 'stock.group_stock_user']),
    ('chief', 'Ігор Савчук', 'Начальник виробництва', 'avatar_chief',
     ['mrp.group_mrp_manager', 'sales_team.group_sale_salesman_all_leads', 'stock.group_stock_user']),
    ('store', 'Марія Гнатюк', 'Комірник', 'avatar_store',
     ['stock.group_stock_manager', 'mrp.group_mrp_user']),
    ('fin', 'Наталія Бондар', 'Фінансист', 'avatar_fin',
     ['sales_team.group_sale_manager', 'account.group_account_user', 'stock.group_stock_user']),
]

# name, company type, city, street: end customers of the factory salon (people and small businesses)
CUSTOMERS = [
    ('Тарас Мельник', 'person', 'Київ', 'вул. Прикладна, 7'), ('Ірина Коваленко', 'person', 'Львів', 'просп. Тестовий, 21'),
    ('Олег Шевчук', 'person', 'Одеса', 'вул. Умовна, 3'), ('Наталія Гончар', 'person', 'Дніпро', 'вул. Зразкова, 15'),
    ('Віктор Бойко', 'person', 'Харків', 'вул. Вигадана, 40'), ('Юлія Романюк', 'person', 'Полтава', 'вул. Центральна, 5'),
    ('Андрій Кравець', 'person', 'Запоріжжя', 'просп. Умовний, 102'), ('Оксана Мороз', 'person', 'Чернівці', 'вул. Зразкова, 9'),
    ('Дмитро Савченко', 'person', 'Житомир', 'вул. Тестова, 31'), ('Марина Поліщук', 'person', 'Вінниця', 'вул. Умовна, 64'),
    ('Кав\'ярня «Зерно»', 'company', 'Київ', 'вул. Прикладна, 88'), ('Студія йоги «Баланс»', 'company', 'Київ', 'вул. Вигадана, 2'),
]

# product, qty, dims (W, H, D), body, facade, edge, fitting, stage, days ago, customer, salesman, discount %, prepay %
ORDERS = [
    # finished (delivered and invoiced)
    ('prod_wardrobe', 1, (1800, 2400, 600), 'sonoma', 'mdf', '2', 'premium', 'done', 29, 0, 'salon', 0, 0),
    ('prod_kitchen', 4, (600, 720, 560), 'white', 'mdf', '04', 'std', 'done', 27, 10, 'salon2', 0, 0),
    ('prod_dresser', 1, (800, 850, 450), 'white', 'mdf', '04', 'std', 'done', 24, 2, 'salon3', 0, 0),
    ('prod_wardrobe', 1, (2000, 2400, 600), 'sonoma', 'mdf', '2', 'std', 'done', 21, 6, 'salon', 8, 0),
    ('prod_dresser', 2, (1000, 900, 450), 'sonoma', 'mdf', '04', 'premium', 'done', 19, 11, 'salon2', 15, 0),
    ('prod_kitchen', 3, (800, 720, 560), 'anthr', 'anthr', '2', 'std', 'done', 17, 4, 'salon3', 0, 0),
    # in production
    ('prod_wardrobe', 1, (1600, 2400, 600), 'sonoma', 'mdf', '2', 'std', 'progress', 9, 1, 'salon', 12, 50),
    ('prod_dresser', 1, (900, 850, 450), 'sonoma', 'mdf', '04', 'std', 'progress', 8, 8, 'salon3', 0, 30),
    ('prod_kitchen', 6, (600, 720, 560), 'white', 'mdf', '04', 'std', 'progress', 8, 10, 'salon2', 10, 50),
    ('prod_wardrobe', 1, (1950, 2400, 600), 'anthr', 'anthr', '2', 'premium', 'progress', 6, 3, 'salon', 0, 50),
    ('prod_dresser', 2, (800, 850, 450), 'white', 'mdf', '04', 'premium', 'progress', 5, 9, 'salon2', 0, 30),
    ('prod_kitchen', 2, (800, 720, 560), 'sonoma', 'mdf', '04', 'std', 'progress', 4, 5, 'salon3', 0, 0),
    # confirmed, waiting for cutting
    ('prod_wardrobe', 1, (1700, 2400, 600), 'sonoma', 'mdf', '2', 'std', 'confirmed', 2, 7, 'salon', 0, 30),
    ('prod_dresser', 1, (800, 850, 450), 'sonoma', 'mdf', '04', 'std', 'confirmed', 2, 0, 'salon2', 0, 0),
    ('prod_kitchen', 3, (600, 720, 560), 'sonoma', 'mdf', '04', 'std', 'confirmed', 2, 11, 'salon3', 0, 50),
    ('prod_wardrobe', 1, (1500, 2400, 600), 'white', 'mdf', '2', 'std', 'confirmed', 0, 5, 'salon2', 0, 0),
    # quotations
    ('prod_wardrobe', 1, (1900, 2400, 600), 'sonoma', 'anthr', '2', 'premium', 'draft', 0, 3, 'salon', 0, 0),
    ('prod_dresser', 1, (1000, 850, 450), 'white', 'mdf', '04', 'std', 'draft', 0, 8, 'salon3', 0, 0),
    ('prod_kitchen', 4, (900, 720, 560), 'anthr', 'anthr', '2', 'std', 'draft', 2, 1, 'salon2', 0, 0),
    ('prod_wardrobe', 1, (1800, 2400, 600), 'white', 'mdf', '2', 'premium', 'draft', 2, 9, 'salon', 0, 0),
    ('prod_dresser', 1, (800, 850, 450), 'anthr', 'anthr', '04', 'std', 'sent', 3, 2, 'salon3', 0, 0),
    ('prod_kitchen', 2, (600, 720, 560), 'sonoma', 'mdf', '2', 'std', 'sent', 4, 6, 'salon2', 0, 0),
    ('prod_wardrobe', 1, (2000, 2400, 600), 'sonoma', 'mdf', '2', 'premium', 'sent', 5, 4, 'salon', 0, 0),
]

NOTES = {
    'sale': [
        ('salon', 'Клієнт погодив декор і розміри, фото замірів у вкладенні до листа.'),
        ('salon', 'Домовились про монтаж після 15-го числа, зателефонувати за день до виїзду.'),
        ('chief', 'Взяв у роботу, запуск на розкрій цього тижня.'),
        ('fin', 'Передоплату отримано, можна запускати.'),
        ('salon', 'Клієнт просить доставку до під\'їзду, підйом на 3-й поверх без ліфта.'),
        ('tech', 'Розміри перевірив: деталі вкладаються в плиту без зайвого відходу.'),
    ],
    'mrp': [
        ('tech', 'Карту розкрою передано на розкрій, ділові обрізки взято в облік.'),
        ('store', 'Плиту й кромку зарезервовано під це замовлення.'),
        ('chief', 'Складання запланував на завтра, бригада №2.'),
        ('store', 'Фурнітуру з комплектом видано на складання.'),
        ('chief', 'Присадку закінчили, передаємо на складання.'),
    ],
}


def _binary(name):
    with file_open(IMG + name, 'rb') as handle:
        return base64.b64encode(handle.read())


def _user(env, login):
    return env['res.users'].search([('login', '=', f'{login}@demo-fabryka.example')], limit=1)


def _note(record, user, text, when=None):
    values = {'body': text, 'message_type': 'comment', 'subtype_xmlid': 'mail.mt_note',
              'author_id': user.partner_id.id}
    if when:
        values['date'] = when
    # the technologist writes in the product card, though the catalogue itself is edited by the sales manager
    (record.sudo() if record._name == 'product.template' else record.with_user(user)).message_post(**values)


def _backdate(env, table, records, when):
    env.cr.execute(f'UPDATE {table} SET create_date = %s WHERE id IN %s', (when, tuple(records.ids)))
    records.invalidate_recordset(['create_date'])


def _localize(env):
    """Ukrainian names for the units and the tax; the demo documents are created in Ukrainian."""
    unit = env.ref('uom.product_uom_unit')
    unit.with_context(lang='en_US').name = 'pcs'
    unit.with_context(lang='uk_UA').name = 'шт'
    for tax in env['account.tax'].search([('amount', '!=', 0.0)]):
        tax.write({'amount': 20.0})
        tax.with_context(lang='en_US').name = 'VAT 20%'
        tax.with_context(lang='uk_UA').name = 'ПДВ 20%'
    for group in env['account.tax'].search([('amount', '=', 20.0)]).tax_group_id:
        group.with_context(lang='en_US').name = 'VAT 20%'
        group.with_context(lang='uk_UA').name = 'ПДВ 20%'
    for xmlid, uk, en in (('uom.product_uom_square_meter', 'м²', 'm²'), ('uom.product_uom_meter', 'м', 'm')):
        unit = env.ref(xmlid)
        unit.with_context(lang='en_US').name = en
        unit.with_context(lang='uk_UA').name = uk
    for pricelist in env['product.pricelist'].search([]):
        pricelist.with_context(lang='en_US').name = 'Retail, UAH'
        pricelist.with_context(lang='uk_UA').name = 'Роздрібний, грн'
    now_term = env.ref('account.account_payment_term_immediate')
    now_term.with_context(lang='en_US').name = 'Payment on receipt'
    now_term.with_context(lang='uk_UA').name = 'Оплата при отриманні'
    env.ref('base.partner_root').write({'lang': 'uk_UA', 'tz': 'Europe/Kyiv'})
    ukraine = env.ref('base.ua')
    ukraine.vat_label = 'ІПН'
    # the sales go to Ukrainian customers: the domestic fiscal position (VAT 20%) applies, not the export one
    env['account.fiscal.position'].search([('name', '=', 'Domestic')]).write({'country_id': ukraine.id})
    for xmlid, text in (('sale.mt_order_confirmed', 'Замовлення підтверджено'), ('sale.mt_order_sent', 'Пропозицію надіслано')):
        env.ref(xmlid).with_context(lang='uk_UA').description = text
    # records created while the module was installed carry English tracking messages
    env['mail.message'].sudo().search([('model', 'in', ('product.template', 'product.product', 'res.partner'))]).unlink()


def _payment_terms(env):
    """Prepayment terms of the factory: x% when the order is confirmed, the rest before delivery."""
    terms = {}
    for percent in (30, 50):
        term = env['account.payment.term'].with_context(lang='en_US').create({
            'name': f'Prepayment {percent}%',
            'line_ids': [(0, 0, {'value': 'percent', 'value_amount': percent, 'delay_type': 'days_after', 'nb_days': 0}),
                         (0, 0, {'value': 'percent', 'value_amount': 100 - percent, 'delay_type': 'days_after', 'nb_days': 14})]})
        term.with_context(lang='uk_UA').name = f'Передоплата {percent}%, решта перед доставкою'
        terms[percent] = term
    terms[0] = env.ref('account.account_payment_term_immediate')
    return terms


def _brand(env):
    company = env.company
    company.write({**COMPANY, 'logo': _binary('logo.png'), 'country_id': env.ref('base.ua').id})
    company.partner_id.write({'image_1920': _binary('logo.png')})
    company.write({'company_registry': '41234567', 'vat': 'UA412345678901'})
    env['res.partner.bank'].create({'acc_number': 'UA21 3223 1300 0002 6007 2335 6600 1', 'partner_id': company.partner_id.id,
                                    'bank_id': env['res.bank'].create({'name': 'Банк «Приклад»', 'bic': 'DEMOUA2K'}).id})
    env.ref('base.user_admin').write({'lang': 'uk_UA', 'tz': 'Europe/Kyiv'})


def _users(env):
    Users = env['res.users'].with_context(no_reset_password=True)
    for login, name, job, avatar, groups in USERS:
        Users.create({
            'name': name, 'login': f'{login}@demo-fabryka.example', 'password': 'demo', 'lang': 'uk_UA',
            'tz': 'Europe/Kyiv', 'image_1920': _binary(avatar + '.png'), 'email': f'{login}@demo-fabryka.example',
            'group_ids': [(6, 0, [env.ref('base.group_user').id] + [env.ref(g).id for g in groups])],
            'notification_type': 'inbox',
        })
    # the job title is shown in the chatter and in the user menu
    for login, name, job, avatar, groups in USERS:
        _user(env, login).partner_id.function = job


def _images(env):
    for key in ('prod_wardrobe', 'prod_dresser', 'prod_kitchen'):
        env.ref(f'td_mebli_demo.{key}').image_1920 = _binary(key + '.png')


def _customers(env, terms):
    partners = env['res.partner']
    first = env.ref('td_mebli_demo.partner_salon')
    for index, (name, kind, city, street) in enumerate(CUSTOMERS):
        vals = {'name': name, 'city': city, 'street': street, 'company_type': kind,
                'country_id': env.ref('base.ua').id, 'phone': f'+380 44 555 02 {index + 10:02d}',
                'email': f'order{index + 1}@client.example', 'lang': 'uk_UA',
                'property_payment_term_id': terms[50 if index % 2 else 30].id}
        if index == 0:
            first.write(vals)
            partners |= first
        else:
            partners |= env['res.partner'].create(vals)
    return partners


def _stock(env, wardrobes):
    """Stock for the show: plenty of everything, the sliding system for wardrobes is short by one set on purpose."""
    from .hooks import _add_stock
    location = env['stock.warehouse'].search([('company_id', '=', env.company.id)], limit=1).lot_stock_id
    target = {'fit_slide': wardrobes, 'fit_hinge': 120, 'fit_guide': 80, 'fit_legs': 200}
    for xmlid, quantity in target.items():
        product = env.ref(f'td_mebli_demo.{xmlid}')
        have = sum(env['stock.quant'].search([('product_id', '=', product.id), ('location_id', '=', location.id)]).mapped('quantity'))
        if have < quantity:
            _add_stock(env, location, product, quantity - have)
        elif have > quantity:
            _add_stock(env, location, product, quantity - have)


def _stamp_workorders(production, order_date, launch_hours, rnd, bias=1.0):
    """Realistic dates and durations for a started or finished work order chain (factory working hours)."""
    cursor = order_date + timedelta(hours=launch_hours)
    for workorder in production.workorder_ids.sorted('id'):
        if workorder.state not in ('progress', 'done'):
            continue
        expected = workorder.duration_expected or 60.0
        real = expected * rnd.uniform(0.92, 1.1) * bias
        start, end = cursor, cursor + timedelta(minutes=real)
        workorder.time_ids.write({'date_start': start, 'date_end': end if workorder.state == 'done' else False})
        workorder.write({'date_start': start, 'date_finished': start + timedelta(minutes=expected)})
        cursor = end + timedelta(minutes=rnd.randint(20, 90))


def _invoice(env, order, when, percent):
    """A down payment invoice (percent) or the invoice for what is delivered; posted and paid on the given date."""
    wizard = env['sale.advance.payment.inv'].with_context(active_model='sale.order', active_ids=order.ids).create(
        {'advance_payment_method': 'percentage' if percent else 'delivered', 'amount': percent or 0.0})
    wizard.create_invoices()
    invoice = order.invoice_ids.filtered(lambda move: move.state == 'draft')
    invoice.write({'invoice_date': when.date(), 'invoice_date_due': when.date()})
    invoice.action_post()
    register = env['account.payment.register'].with_context(
        active_model='account.move', active_ids=invoice.ids).create({'payment_date': when.date()})
    register._create_payments()


def _deliver(order):
    for picking in order.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')):
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        picking.with_context(skip_backorder=True, skip_sms=True).button_validate()


def _age_system_messages(env):
    """System messages (creation, confirmation, payment) get the dates of their documents, not the seeding time."""
    env.flush_all()

    def fix(records, base_of):
        for record in records:
            base = base_of(record)
            if not base:
                continue
            messages = env['mail.message'].search([
                ('model', '=', record._name), ('res_id', '=', record.id), ('message_type', '!=', 'comment')], order='id')
            for index, message in enumerate(messages):
                env.cr.execute('UPDATE mail_message SET date = %s WHERE id = %s',
                               (base + timedelta(minutes=3 * (index + 1)), message.id))
    fix(env['sale.order'].search([]), lambda order: order.date_order)
    fix(env['mrp.production'].search([]),
        lambda mo: (mo.reference_ids.sale_ids[:1].date_order or fields.Datetime.now()) + timedelta(hours=20))
    fix(env['td.mebli.cutting.job'].search([]), lambda job: job.create_date)
    fix(env['account.move'].search([('move_type', '=', 'out_invoice')]),
        lambda move: fields.Datetime.to_datetime(move.invoice_date) + timedelta(hours=10) if move.invoice_date else False)
    # the system writes on behalf of the root bot; in a live factory these records are created by people
    bot = env.ref('base.partner_root').id
    for model, login in (('mrp.production', 'chief'), ('td.mebli.cutting.job', 'tech'), ('account.move', 'fin'),
                         ('stock.picking', 'store'), ('mrp.workorder', 'chief')):
        env.cr.execute('UPDATE mail_message SET author_id = %s WHERE model = %s AND author_id = %s',
                       (_user(env, login).partner_id.id, model, bot))
    env.invalidate_all()


def seed_showcase(env):
    rnd = random.Random(2026)
    env = env(context=dict(env.context, lang='uk_UA'))
    now = fields.Datetime.now()
    if env['sale.order'].search_count([('state', '!=', 'cancel')], limit=1):
        return {}
    _localize(env)
    _brand(env)
    _users(env)
    _images(env)
    terms = _payment_terms(env)
    partners = _customers(env, terms)
    wardrobes = sum(1 for row in ORDERS if row[0] == 'prod_wardrobe' and row[7] != 'draft' and row[7] != 'sent')
    _stock(env, wardrobes)
    people = {login: _user(env, login) for login, *_ in USERS}

    orders = {'done': env['sale.order'], 'progress': env['sale.order'], 'confirmed': env['sale.order']}
    prepay, drafts = [], env['sale.order']
    for product, qty, dims, body, facade, edge, fitting, stage, days, customer, seller, discount, advance in ORDERS:
        order = make_order(env, product, dims, f'val_body_{body}', f'val_facade_{facade}', f'val_edge_{edge}',
                           f'val_fit_{fitting}', qty=float(qty))
        ordered = now - timedelta(days=days, hours=rnd.randint(0, 5))
        order.write({'partner_id': partners[customer].id, 'user_id': people[seller].id, 'date_order': ordered,
                     'payment_term_id': terms[advance if advance in terms else 0].id, 'validity_date': (ordered + timedelta(days=14)).date(),
                     'note': 'Термін виготовлення — 14 робочих днів від дня передоплати. Гарантія на виріб — 24 місяці. Доставка й монтаж за окремою домовленістю.'})
        order = order.with_user(people[seller])
        order.order_line.action_td_generate_bom()
        if discount:
            order.order_line.discount = discount
        if stage == 'sent':
            order.action_quotation_sent()
            drafts |= order.with_env(env)
        elif stage == 'draft':
            drafts |= order.with_env(env)
        else:
            order.action_confirm()
            order.date_order = ordered  # confirmation stamps the current time: put the order date back
            orders[stage] |= order.with_env(env)
            if advance:
                prepay.append((order.with_env(env), advance))
    # chatter on orders: several roles, dates spread between the order date and now
    for order in (orders['done'] | orders['progress'] | orders['confirmed']):
        span = max((now - order.date_order).total_seconds(), 3600.0)
        for position, (author, text) in enumerate(rnd.sample(NOTES['sale'], 3)):
            when = order.date_order + timedelta(seconds=span * (position + 1) / 4.0)
            # the salesperson writes only in the orders of her own
            _note(order, order.user_id if author == 'salon' else people[author], text, when)
    for order in drafts:
        quote_day = order.date_order + timedelta(hours=3)
        _note(order, people[order.user_id.login.split('@')[0]], 'Надіслала клієнту візуалізацію й попередню ціну, чекаємо відповідь.', quote_day)

    # history: finished orders and orders in progress go through cutting in several jobs, like the live ones
    jobs = env['td.mebli.cutting.job']
    batches = [(orders['done'][:3], 'done', 28), (orders['done'][3:], 'done', 20),
               (orders['progress'][:3], 'progress', 9), (orders['progress'][3:], 'progress', 5)]
    for batch, stage, days in batches:
        tech = people['tech']
        job = env['td.mebli.cutting.job'].with_user(tech).create({'production_ids': [(6, 0, batch.mrp_production_ids.ids)]})
        job.action_send()
        job.action_simulate()
        job.action_done()
        when = now - timedelta(days=days, hours=-rnd.randint(1, 4))
        _backdate(env, 'td_mebli_cutting_job', job, when)
        for lot in job.sheet_ids.offcut_ids.lot_id:  # the offcuts of one job are stocked during the shift, not in one minute
            _backdate(env, 'stock_lot', lot, when + timedelta(minutes=rnd.randint(5, 420)))
        _note(job, tech, 'Результат розкрою прийнято, обрізки від листів взято в облік.', when + timedelta(hours=1))
        jobs |= job
        for order in batch:
            production = order.mrp_production_ids
            launch = rnd.randint(14, 44)
            levels = 4 if stage == 'done' else rnd.randint(1, 3)
            for position, workorder in enumerate(production.workorder_ids.sorted('id')):
                if position < levels:
                    workorder.button_start()
                    if stage == 'done' or position < levels - 1:
                        workorder.button_finish()
            bias = 1.0
            if stage == 'done' and order == orders['done'][3]:
                bias = 1.22  # one order took longer than planned: a deviation worth showing
            _stamp_workorders(production, order.date_order, launch, rnd, bias)
            if stage == 'done':
                for move in production.move_raw_ids:
                    # the real consumption differs a little from the plan: an extra sheet cut, a longer edge strip
                    factor = {'ЛДСП': 1.06, 'КР': 1.04, 'МДФ': 0.97}.get((move.product_id.default_code or '').split('-')[0])
                    if factor and move.product_uom_qty:
                        move.quantity = round(move.product_uom_qty * factor, 3)
                        move.picked = True
                production.with_context(skip_consumption=True, skip_backorder=True).button_mark_done()
                production.write({'date_finished': production.workorder_ids.sorted('id')[-1].date_finished})
            production.date_deadline = order.date_order + timedelta(days=rnd.randint(12, 16))
            for position, (author, text) in enumerate(rnd.sample(NOTES['mrp'], 3)):
                _note(production, people[author], text, order.date_order + timedelta(hours=launch + 6 * (position + 1)))
    # one order in production is late: the deadline has passed
    late = orders['progress'][1].mrp_production_ids
    # invoices and payments: delivered orders are paid in full, many orders in work have a prepayment
    for order in orders['done']:
        _deliver(order)
        _invoice(env, order, order.date_order + timedelta(days=rnd.randint(8, 12)), 0)
    for order, percent in prepay:
        _invoice(env, order, order.date_order + timedelta(hours=26), percent)
        _note(order, people['fin'], f'Передоплату {percent}% отримано, замовлення можна запускати.',
              order.date_order + timedelta(hours=27))
    # work waiting for cutting: planned work orders, so that the work centers show their load
    waiting = orders['confirmed'].mrp_production_ids
    waiting.button_plan()
    for production in waiting:
        production.date_deadline = production.sudo().reference_ids.sale_ids[:1].date_order + timedelta(days=14)
    # extra business offcuts of the main decors on the shelf (from earlier jobs): the next cutting uses them first
    from .hooks import _add_stock
    location = env['stock.warehouse'].search([('company_id', '=', env.company.id)], limit=1).lot_stock_id
    Lot = env['stock.lot']
    for xmlid, sizes in {'board_sonoma': [(1900, 850), (1350, 960), (1100, 640)],
                         'board_white': [(1700, 900), (1200, 700), (980, 620)],
                         'board_anthr': [(1500, 800), (1050, 700)]}.items():
        product = env.ref(f'td_mebli_demo.{xmlid}')
        for length, width in sizes:
            job = jobs[rnd.randrange(len(jobs))]
            lot = Lot.create({'name': f'ОБР-{product.default_code}-{Lot.search_count([("product_id", "=", product.id), ("td_is_offcut", "=", True)]) + 1}',
                              'product_id': product.id, 'td_length_mm': length, 'td_width_mm': width,
                              'td_is_offcut': True, 'td_cutting_job_id': job.id})
            _add_stock(env, location, product, lot.td_area_m2, lot)
            _backdate(env, 'stock_lot', lot, job.create_date + timedelta(hours=rnd.randint(1, 5), minutes=rnd.randint(0, 59)))
    # deadlines against the planned finish: most orders fit, two do not (one already late, one will be late)
    open_productions = env['mrp.production'].search([('state', 'in', ('confirmed', 'progress', 'to_close'))])
    for production in open_productions:
        finish = production.date_finished or now
        production.date_deadline = finish + timedelta(days=rnd.randint(2, 6))
    late.date_deadline = now - timedelta(days=2)
    (waiting[:1]).date_deadline = (waiting[:1].date_finished or now) - timedelta(days=1)
    for production in env['mrp.production'].search([('state', '=', 'done')]):
        production.date_deadline = production.date_finished + timedelta(days=rnd.randint(1, 4))
    # who is responsible and what the shop floor wrote down
    for production in env['mrp.production'].search([]):
        production.user_id = people['chief' if production.state != 'confirmed' else 'tech']
    for production in waiting:
        _note(production, people['chief'], 'Передано технологу: перевірити розміри перед розкроєм.', now - timedelta(hours=rnd.randint(2, 9)))
        _note(production, people['store'], 'Плиту й кромку зарезервовано. Розсувну систему замовлено, очікуємо поставку.', now - timedelta(hours=rnd.randint(1, 7)))
    for key, text in (('prod_wardrobe', 'Максимальна ширина без стику задньої стінки — 2060 мм, більше — окремим замовленням.'),
                      ('prod_kitchen', 'Фасади лише з МДФ; кромка ПВХ 2 мм обов\'язкова для відкритих торців.'),
                      ('prod_dresser', 'Стандартна висота цоколя 100 мм, регульовані опори в комплекті.')):
        _note(env.ref(f'td_mebli_demo.{key}'), people['tech'], text, now - timedelta(days=rnd.randint(20, 35)))
    _age_system_messages(env)
    # no chatter message dated «yesterday»: the web client shows that word untranslated, a plain date reads better
    env.cr.execute("""UPDATE mail_message SET date = date - interval '1 day' WHERE date >= (date_trunc('day', now() at time zone 'Europe/Kyiv') - interval '1 day') at time zone 'Europe/Kyiv'
                      AND date < date_trunc('day', now() at time zone 'Europe/Kyiv') at time zone 'Europe/Kyiv'""")
    env.flush_all()
    return {'orders': env['sale.order'].search_count([]), 'productions': env['mrp.production'].search_count([])}
