"""Showcase data of the demo factory: branding, role users, a living order book.

seed_showcase(env) runs once on a database that already has td_mebli_demo (catalog, stock). It is used for the
sales demo (docs/industries/mebli/prototype-real/): 22 orders in different stages, invoices and prepayments,
manufacturing orders with work orders in progress, finished cutting jobs with business offcuts, chatter history
written by different roles. Everything is fictional: company, people, customers, addresses and phones.
It uses only public ORM methods of the packages.
"""
import base64
import math
import random
from datetime import timedelta, timezone
from zoneinfo import ZoneInfo

from odoo import fields
from odoo.tools import file_open

from .dates import seed_dates
from .scenario import make_order

IMG = 'td_mebli_demo/static/img/'

COMPANY = {
    'name': 'Меблева фабрика «Демо»', 'street': 'вул. Заводська, 12', 'city': 'Київ', 'zip': '02000',
    'phone': '+380 00 000 00 01', 'email': 'office@demo-fabryka.example', 'website': 'https://demo-fabryka.example',
    'primary_color': '#3d2b1f', 'secondary_color': '#c9a06a',
}

# login, name, job, avatar, groups (xmlids)
USERS = [
    # the salon manager reads the purchases of her orders read only (td_mebli_sale: access rule «purchases of my orders»);
    # no Purchase group: the smart button of sale_purchase stays with the buyers, as in the standard
    ('salon', 'Олена Мартинюк', 'Менеджер салону', 'avatar_salon', ['sales_team.group_sale_salesman']),
    ('salon2', 'Роман Лисенко', 'Менеджер салону', 'avatar_salon2', ['sales_team.group_sale_salesman']),
    ('salon3', 'Світлана Прокопенко', 'Менеджер салону', 'avatar_salon3', ['sales_team.group_sale_salesman']),
    ('tech', 'Андрій Ковальчук', 'Технолог-конструктор', 'avatar_tech',
     ['mrp.group_mrp_user', 'sales_team.group_sale_salesman_all_leads', 'stock.group_stock_user']),
    ('chief', 'Ігор Савчук', 'Начальник виробництва', 'avatar_chief',
     ['mrp.group_mrp_manager', 'sales_team.group_sale_salesman_all_leads', 'stock.group_stock_user']),
    ('store', 'Марія Гнатюк', 'Комірник', 'avatar_store',
     ['stock.group_stock_manager', 'mrp.group_mrp_user', 'purchase.group_purchase_user', 'stock.group_stock_user']),
    ('fin', 'Наталія Бондар', 'Фінансист', 'avatar_fin',
     ['sales_team.group_sale_manager', 'account.group_account_user', 'stock.group_stock_user',
      'td_mebli_dashboard.group_td_mebli_director']),
    ('owner', 'Віталій Остапенко', 'Власник · директор фабрики', 'avatar_owner',
     ['sales_team.group_sale_manager', 'mrp.group_mrp_manager', 'account.group_account_user', 'stock.group_stock_user',
      'purchase.group_purchase_manager', 'project.group_project_manager', 'td_mebli_dashboard.group_td_mebli_director']),
    # full scope (A-21, wave 1): measurer, installers, the shared tablet of the shop (no picture: initials avatar)
    ('measure', 'Тетяна Олійник', 'Замірник', None,
     ['sales_team.group_sale_salesman_all_leads', 'td_mebli_measure.group_td_mebli_measurer']),
    ('fitter', 'Микола Демченко', 'Бригадир монтажників', None,
     ['project.group_project_user', 'sales_team.group_sale_salesman_all_leads']),
    ('fitter2', 'Іван Кушнір', 'Монтажник', None, ['project.group_project_user', 'sales_team.group_sale_salesman_all_leads']),
    ('tablet', 'Планшет цеху', 'Планшет дільниць', None, ['mrp.group_mrp_user']),
]

# name, company type, city, street: end customers of the factory salon (people and small businesses)
CUSTOMERS = [
    ('Тарас Мельник', 'person', 'Київ', 'вул. Липова, 7'), ('Ірина Коваленко', 'person', 'Львів', 'просп. Стрийська, 21'),
    ('Олег Шевчук', 'person', 'Одеса', 'вул. Садова, 3'), ('Наталія Гончар', 'person', 'Дніпро', 'вул. Шевченка, 15'),
    ('Віктор Бойко', 'person', 'Харків', 'вул. Берестейська, 40'), ('Юлія Романюк', 'person', 'Полтава', 'вул. Центральна, 5'),
    ('Андрій Кравець', 'person', 'Запоріжжя', 'просп. Перемоги, 102'), ('Оксана Мороз', 'person', 'Чернівці', 'вул. Лесі Українки, 9'),
    ('Дмитро Савченко', 'person', 'Житомир', 'вул. Франка, 31'), ('Марина Поліщук', 'person', 'Вінниця', 'вул. Соборна, 64'),
    ('Кав\'ярня «Зерно»', 'company', 'Київ', 'вул. Липова, 88'), ('Студія йоги «Баланс»', 'company', 'Київ', 'вул. Берестейська, 2'),
    ('Будинок «Липки» (забудовник)', 'company', 'Київ', 'вул. Незалежності, 150'), ('Готель «Затишок»', 'company', 'Львів', 'вул. Героїв Майдану, 12'),
    ('Офіс-центр «Вузол»', 'company', 'Дніпро', 'просп. Науки, 8'), ('Мережа клінік «Здоров\'я»', 'company', 'Одеса', 'вул. Берестейська, 77'),
    ('ЖК «Сонячний квартал»', 'company', 'Харків', 'вул. Центральна, 3'), ('Хостел «Подорож»', 'company', 'Київ', 'вул. Липова, 19'),
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


_KYIV = ZoneInfo('Europe/Kyiv')


def _section_calendar(env, center, weekly_hours):
    """A standard working calendar of a section: Mon-Fri from 8:00, the same share of the day every day."""
    per_day = weekly_hours / 5.0
    calendar = env['resource.calendar'].create({
        'name': f'{center.name}: {weekly_hours} год на тиждень', 'tz': 'Europe/Kyiv',
        'company_id': center.company_id.id or env.company.id})
    # the default attendances of a new calendar (company calendar) are replaced, not added to
    calendar.write({
        'attendance_ids': [(5, 0, 0)] + [
            (0, 0, {'name': f'{center.name} {day + 1}', 'dayofweek': str(day), 'hour_from': 8.0, 'hour_to': 8.0 + per_day,
                    'day_period': 'morning'})
            for day in range(5)],
    })
    return calendar


def _work(when, rnd=None):
    """Move a naive UTC datetime into factory working hours (Mon-Fri, 8:00-17:00 Kyiv time); returns naive UTC."""
    local = when.replace(tzinfo=timezone.utc).astimezone(_KYIV)
    if local.hour >= 17:
        local = (local + timedelta(days=1)).replace(hour=8, minute=(rnd.randint(5, 50) if rnd else 15))
    elif local.hour < 8:
        local = local.replace(hour=8, minute=(rnd.randint(5, 50) if rnd else 15))
    while local.weekday() >= 5:
        local = (local + timedelta(days=1)).replace(hour=8, minute=(rnd.randint(5, 50) if rnd else 15))
    return local.astimezone(timezone.utc).replace(tzinfo=None)


def _past(raw, now, rnd=None):
    """Working-hours time not later than an hour ago: the demo never shows dates from the future."""
    when = _work(raw, rnd)
    while when > now - timedelta(hours=1):
        raw -= timedelta(days=1)
        when = _work(raw, rnd)
    return when


def _bulk_orders(rnd):
    """The rest of the order book of a working factory: ~80 orders over two months, in the same tuple format."""
    rows = []

    def one(stage, days, discount=0, advance=None):
        kind = rnd.choice(['prod_wardrobe', 'prod_wardrobe', 'prod_kitchen', 'prod_kitchen', 'prod_dresser'])
        if kind == 'prod_wardrobe':
            qty, dims = rnd.choice([1, 2, 2, 3]), (rnd.choice(range(1500, 2051, 50)), 2400, 600)
        elif kind == 'prod_kitchen':
            qty, dims = rnd.randint(7, 16), (rnd.choice([600, 800, 900]), 720, 560)
        else:
            qty, dims = rnd.randint(2, 6), (rnd.choice([800, 900, 1000]), 850, 450)
        body = rnd.choice(['sonoma', 'white', 'anthr'])
        facade = 'anthr' if body == 'anthr' else 'mdf'
        advance = rnd.choice([0, 30, 50]) if advance is None else advance
        rows.append((kind, qty, dims, body, facade, rnd.choice(['04', '2']), rnd.choice(['std', 'std', 'premium']),
                     stage, days, rnd.randrange(len(CUSTOMERS)), rnd.choice(['salon', 'salon2', 'salon3']), discount, advance))
    for _ in range(49):
        one('done', rnd.randint(31, 58), discount=rnd.choice([0, 0, 0, 5, 8, 10]))
    for _ in range(2):
        one('done', rnd.randint(33, 55), discount=-1)
    for _ in range(20):
        one('done', rnd.randint(9, 28), discount=rnd.choice([0, 0, 0, 5, 8, 10]))
    for _ in range(3):
        one('done', rnd.randint(12, 27), discount=-1)
    for _ in range(12):
        one('progress', rnd.randint(2, 8), discount=rnd.choice([0, 0, 5, 8, 10]), advance=rnd.choice([30, 50]))
    for _ in range(6):
        one('confirmed', rnd.randint(0, 2), advance=rnd.choice([0, 30, 50]))
    for _ in range(4):
        one('draft', rnd.randint(0, 3))
    for _ in range(3):
        one('sent', rnd.randint(2, 6))
    return rows


def _binary(name):
    with file_open(IMG + name, 'rb') as handle:
        return base64.b64encode(handle.read())


def _user(env, login):
    return env['res.users'].search([('login', '=', f'{login}@demo-fabryka.example')], limit=1)


def _note(record, user, text, when=None):
    values = {'body': text, 'message_type': 'comment', 'subtype_xmlid': 'mail.mt_note',
              'author_id': user.partner_id.id}
    if when:
        values['date'] = min(when, fields.Datetime.now() - timedelta(minutes=30))
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
    """Prepayment terms of the factory: x% when the order is confirmed, the rest before delivery; and the schedule of
    the A box (F-22): 50 % prepayment, 40 % before the installation, 10 % after the act. The milestone of a line
    (td_mebli_sale) tells the payment control which lines are due before the crew goes (td_mebli_install)."""
    terms = {}
    for percent in (30, 50):
        term = env['account.payment.term'].with_context(lang='en_US').create({
            'name': f'Prepayment {percent}%',
            'line_ids': [(0, 0, {'value': 'percent', 'value_amount': percent, 'delay_type': 'days_after', 'nb_days': 0,
                                 'td_milestone': 'order'}),
                         (0, 0, {'value': 'percent', 'value_amount': 100 - percent, 'delay_type': 'days_after', 'nb_days': 14,
                                 'td_milestone': 'install'})]})
        term.with_context(lang='uk_UA').name = f'Передоплата {percent}%'  # the rest before delivery: the term lines say it
        terms[percent] = term
    term = env['account.payment.term'].with_context(lang='en_US').create({
        'name': '50% prepayment, 40% before installation, 10% after the act',
        'note': '<p>50 % — передоплата при підписанні договору; 40 % — перед монтажем; 10 % — після підписання акта монтажу.</p>',
        'line_ids': [(0, 0, {'value': 'percent', 'value_amount': 50, 'delay_type': 'days_after', 'nb_days': 0, 'td_milestone': 'order'}),
                     (0, 0, {'value': 'percent', 'value_amount': 40, 'delay_type': 'days_after', 'nb_days': 21, 'td_milestone': 'install'}),
                     (0, 0, {'value': 'percent', 'value_amount': 10, 'delay_type': 'days_after', 'nb_days': 35, 'td_milestone': 'act'})]})
    term.with_context(lang='uk_UA').name = '50 % передоплата, 40 % перед монтажем, 10 % після акта'
    terms['schedule'] = term
    terms[0] = env.ref('account.account_payment_term_immediate')
    return terms


def _brand(env):
    company = env.company
    company.write({**COMPANY, 'logo': _binary('logo.png'), 'country_id': env.ref('base.ua').id})
    company.partner_id.write({'image_1920': _binary('logo.png')})
    # registry code of a fictional format (no real EDRPOU check passes), no bank account (demo-data-rules.md)
    company.write({'company_registry': 'ДЕМО-0001'})
    env.ref('base.user_admin').write({'lang': 'uk_UA', 'tz': 'Europe/Kyiv'})


def _users(env):
    Users = env['res.users'].with_context(no_reset_password=True)
    for login, name, job, avatar, groups in USERS:
        Users.create({
            'name': name, 'login': f'{login}@demo-fabryka.example', 'password': 'demo', 'lang': 'uk_UA',
            'tz': 'Europe/Kyiv', 'image_1920': _binary(avatar + '.png') if avatar else False,
            'email': f'{login}@demo-fabryka.example',
            'group_ids': [(6, 0, [env.ref('base.group_user').id] + [env.ref(g).id for g in groups])],
            'notification_type': 'inbox', 'odoobot_state': 'disabled',  # no OdooBot onboarding window on the first login
        })
    # the job title is shown in the chatter and in the user menu
    for login, name, job, avatar, groups in USERS:
        _user(env, login).partner_id.function = job


def _images(env):
    for key in ('prod_wardrobe', 'prod_dresser', 'prod_kitchen'):
        env.ref(f'td_mebli_demo.{key}').image_1920 = _binary(key + '.png')


_CITY_CODE = {'Київ': '44', 'Львів': '32', 'Одеса': '48', 'Дніпро': '56', 'Харків': '57', 'Полтава': '532', 'Запоріжжя': '61',
              'Чернівці': '372', 'Житомир': '412', 'Вінниця': '432'}
_TR = dict(zip('абвгґдезийклмнопрстуфцьіїє', 'abvhgdezyyklmnoprstufc\'iie'))
_TR.update({'ж': 'zh', 'х': 'kh', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ю': 'iu', 'я': 'ia', 'ь': '', "'": '', '\u2019': ''})


def _phone(index, city):
    # fictional numbers of the format +380 00 000 00 NN (demo-data-rules.md): no real subscriber is reached
    return f'+380 00 000 00 {(index + 10) % 100:02d}'


def _email(name, kind, index):
    """Plausible e-mail from the name of a private person (surname@mail), or info@ for a company."""
    words = name.lower().split()
    if kind == 'company':
        return f'office{index + 1}@client-demo.example'
    latin = ''.join(_TR.get(ch, ch if ch.isascii() and ch.isalnum() else '') for ch in words[-1])
    first = ''.join(_TR.get(ch, '') for ch in words[0])[:1]
    return f'{first}.{latin}@mail.example'


def _customers(env, terms):
    partners = env['res.partner']
    first = env.ref('td_mebli_demo.partner_salon')
    for index, (name, kind, city, street) in enumerate(CUSTOMERS):
        vals = {'name': name, 'city': city, 'street': street, 'company_type': kind,
                'country_id': env.ref('base.ua').id, 'phone': _phone(index, city),
                'email': _email(name, kind, index), 'lang': 'uk_UA',
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
    target = {'fit_slide': wardrobes, 'fit_hinge': 900, 'fit_guide': 500, 'fit_legs': 1000}
    for xmlid, quantity in target.items():
        product = env.ref(f'td_mebli_demo.{xmlid}')
        have = sum(env['stock.quant'].search([('product_id', '=', product.id), ('location_id', '=', location.id)]).mapped('quantity'))
        if have < quantity:
            _add_stock(env, location, product, quantity - have)
        elif have > quantity:
            _add_stock(env, location, product, quantity - have)


def _stock_up(env):
    """A working factory keeps months of material: the sheets (each with a lot), the edge and the fittings, in bulk."""
    from .hooks import SHEET_L, SHEET_W, SHEETS, EDGE_METRES, _add_stock
    location = env['stock.warehouse'].search([('company_id', '=', env.company.id)], limit=1).lot_stock_id
    Lot, Quant = env['stock.lot'], env['stock.quant'].with_context(inventory_mode=True)
    more_sheets = {'board_sonoma': 170, 'board_white': 170, 'board_anthr': 120, 'board_mdf': 130, 'board_hdf': 120}
    quants = []
    for xmlid, total in more_sheets.items():
        product = env.ref(f'td_mebli_demo.{xmlid}')
        lots = Lot.create([{'name': f'{product.default_code}-{index:03d}', 'product_id': product.id,
                            'td_length_mm': SHEET_L, 'td_width_mm': SHEET_W} for index in range(SHEETS[xmlid] + 1, total + 1)])
        quants += [Quant.create({'product_id': product.id, 'location_id': location.id, 'lot_id': lot.id,
                                 'inventory_quantity': lot.td_area_m2}) for lot in lots]
    env['stock.quant'].browse([q.id for q in quants]).action_apply_inventory()
    for xmlid, metres in EDGE_METRES.items():
        _add_stock(env, location, env.ref(f'td_mebli_demo.{xmlid}'), metres * 7)


def _stamp_workorders(production, order_date, launch_hours, rnd, bias=1.0):
    """Realistic dates and durations for a started or finished work order chain (factory working hours)."""
    cursor = _work(order_date + timedelta(hours=launch_hours), rnd)
    for workorder in production.workorder_ids.sorted('id'):
        if workorder.state not in ('progress', 'done'):
            continue
        expected = workorder.duration_expected or 60.0
        real = expected * rnd.uniform(0.92, 1.1) * bias
        start, end = cursor, cursor + timedelta(minutes=real)
        workorder.time_ids.write({'date_start': start, 'date_end': end if workorder.state == 'done' else False})
        workorder.write({'date_start': start, 'date_finished': start + timedelta(minutes=expected)})
        cursor = _work(end + timedelta(minutes=rnd.randint(20, 90)), rnd)


def _invoice(env, order, when, percent):
    """A down payment invoice (percent) or the invoice for what is delivered; posted and paid on the given date."""
    wizard = env['sale.advance.payment.inv'].with_context(active_model='sale.order', active_ids=order.ids).create(
        {'advance_payment_method': 'percentage' if percent else 'delivered', 'amount': percent or 0.0})
    wizard.create_invoices()
    invoice = order.invoice_ids.filtered(lambda move: move.state == 'draft')
    invoice.write({'invoice_date': when.date(), 'invoice_date_due': when.date()})
    invoice.action_post()
    register = env['account.payment.register'].with_context(
        active_model='account.move', active_ids=invoice.ids).create(
        {'payment_date': when.date(), 'amount': sum(invoice.mapped('amount_residual'))})  # all installments, not the first
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
    # td_no_forecast_activity: the activities «forecast date shift» are made once at the end (wave2), not for every
    # intermediate date of the seed
    env = env(context=dict(env.context, lang='uk_UA', td_no_forecast_activity=True))
    now = fields.Datetime.now()
    if env['sale.order'].search_count([('state', '!=', 'cancel')], limit=1):
        return {}
    # the company currency is UAH before the first document (the post-init hook may run before the chart of accounts
    # is loaded, which sets USD): without it the dashboard and the payments are in dollars
    from .hooks import _set_company_currency
    _set_company_currency(env)
    _localize(env)
    _brand(env)
    _users(env)
    _images(env)
    terms = _payment_terms(env)
    partners = _customers(env, terms)
    bulk = _bulk_orders(random.Random(7))
    wardrobes = sum(row[1] for row in ORDERS + bulk if row[0] == 'prod_wardrobe' and row[7] not in ('draft', 'sent'))
    _stock_up(env)
    _stock(env, wardrobes)
    people = {login: _user(env, login) for login, *_ in USERS}

    from .full import _installation_project, seed_full
    _project, install = _installation_project(env)
    orders = {'done': env['sale.order'], 'progress': env['sale.order'], 'confirmed': env['sale.order']}
    prepay, drafts = [], env['sale.order']
    for product, qty, dims, body, facade, edge, fitting, stage, days, customer, seller, discount, advance in ORDERS + bulk:
        order = make_order(env, product, dims, f'val_body_{body}', f'val_facade_{facade}', f'val_edge_{edge}',
                           f'val_fit_{fitting}', qty=float(qty))
        ordered = _past(now - timedelta(days=days, hours=rnd.randint(0, 5)), now, rnd)
        order.write({'partner_id': partners[customer].id, 'user_id': people[seller].id, 'date_order': ordered,
                     'payment_term_id': terms[advance or 30].id, 'validity_date': (ordered + timedelta(days=14)).date(),
                     'note': 'Термін виготовлення — 14 робочих днів від дня передоплати. Гарантія на виріб — 24 місяці. Доставка й монтаж за окремою домовленістю.'})
        order = order.with_user(people[seller])
        order.order_line.action_td_generate_bom()
        if discount == -1:  # a deal sold almost at cost: the discount that brings the margin down to 6-13%
            line = order.order_line[:1]
            target = rnd.choice([0.06, 0.09, 0.13])
            discount = max(0.0, round((1 - line.purchase_price / (line.price_unit * (1 - target))) * 100.0, 1))
        if discount:
            order.order_line.discount = discount
        # delivery and installation are in the price of the order; the service line makes the visit task (sale_project)
        order.order_line = [(0, 0, {'product_id': install.id, 'product_uom_qty': 1.0})]
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
        old = order.date_order < now - timedelta(days=30)
        for position, (author, text) in enumerate(rnd.sample(NOTES['sale'], 1 if old else 3)):
            when = order.date_order + timedelta(seconds=span * (position + 1) / 4.0)
            # the salesperson writes only in the orders of her own
            _note(order, order.user_id if author == 'salon' else people[author], text, when)
    for order in drafts:
        quote_day = order.date_order + timedelta(hours=3)
        _note(order, people[order.user_id.login.split('@')[0]], 'Надіслала клієнту візуалізацію й попередню ціну, чекаємо відповідь.', quote_day)

    # history: finished orders and orders in progress go through cutting in several jobs, like the live ones
    jobs = env['td.mebli.cutting.job']
    dev_order = orders['done'][3]  # the order that took longer than planned: a deviation worth showing
    batches = []
    for stage in ('done', 'progress'):
        ordered_list = orders[stage].sorted('date_order')
        for index in range(0, len(ordered_list), 4):
            batches.append((ordered_list[index:index + 4], stage))
    for batch, stage in batches:
        tech = people['tech']
        job = env['td.mebli.cutting.job'].with_user(tech).create({'production_ids': [(6, 0, batch.mrp_production_ids.ids)]})
        job.action_send()
        job.action_simulate()
        job.action_done()
        when = _past(max(batch.mapped('date_order')) + timedelta(hours=rnd.randint(20, 40)), now, rnd)
        _backdate(env, 'td_mebli_cutting_job', job, when)
        for lot in job.sheet_ids.offcut_ids.lot_id:  # the offcuts of one job are stocked during the shift, not in one minute
            _backdate(env, 'stock_lot', lot, _work(when + timedelta(minutes=rnd.randint(5, 420)), rnd))
        _note(job, tech, 'Результат розкрою прийнято, обрізки від листів взято в облік.', when + timedelta(hours=1))
        jobs |= job
        for order in batch:
            production = order.mrp_production_ids
            launch = rnd.randint(14, 44) if order.date_order >= now - timedelta(days=30) else rnd.randint(26, 60)
            levels = 4 if stage == 'done' else rnd.randint(1, 3)
            for position, workorder in enumerate(production.workorder_ids.sorted('id')):
                if position < levels:
                    workorder.button_start()
                    if stage == 'done' or position < levels - 1:
                        workorder.button_finish()
            bias = 1.0
            if stage == 'done' and order == dev_order:
                bias = 1.22  # one order took longer than planned: a deviation worth showing
            _stamp_workorders(production, order.date_order, launch, rnd, bias)
            if stage == 'done':
                for move in production.move_raw_ids:
                    # the real consumption differs a little from the plan: an extra sheet cut, a longer edge strip
                    # (tracked sheets are consumed by their lots exactly as the cutting job reserved them)
                    factor = {'КР': 1.08}.get((move.product_id.default_code or '').split('-')[0])
                    if factor and move.product_uom_qty and move.has_tracking == 'none':
                        move.quantity = round(move.product_uom_qty * factor, 3)
                        move.picked = True
                production.with_context(skip_consumption=True, skip_backorder=True).button_mark_done()
                production.write({'date_finished': production.workorder_ids.sorted('id')[-1].date_finished})
            production.date_deadline = order.date_order + timedelta(days=rnd.randint(12, 16))
            for position, (author, text) in enumerate(rnd.sample(NOTES['mrp'], 1 if order.date_order < now - timedelta(days=30) else 3)):
                _note(production, people[author], text, order.date_order + timedelta(hours=launch + 6 * (position + 1)))
    # one order in production is late: the deadline has passed
    late = orders['progress'][1].mrp_production_ids
    # invoices and payments: delivered orders are paid in full, many orders in work have a prepayment
    # the prepayment comes first, the final invoice of a delivered order deducts it (standard down payment)
    for order, percent in prepay:
        _invoice(env, order, order.date_order + timedelta(hours=26), percent)
        _note(order, people['fin'], f'Передоплату {percent}% отримано, замовлення можна запускати.',
              order.date_order + timedelta(hours=27))
    for order in orders['done']:
        _deliver(order)
        _invoice(env, order, order.date_order + timedelta(days=rnd.randint(8, 12)), 0)
    # work waiting for cutting: planned work orders, so that the work centers show their load
    waiting = orders['confirmed'].mrp_production_ids
    waiting.button_plan()
    # the queue of waiting orders is laid out over the next 2-3 weeks (the bottleneck is shown by the load chart, not by a
    # plan stretched over months): each order starts a day or so after the previous one
    for index, production in enumerate(waiting.sorted('id')):
        cursor = _work(now + timedelta(days=1 + index * 1.2), rnd)
        first = None
        for workorder in production.workorder_ids.sorted('id'):
            hours = min(max((workorder.duration_expected or 60.0) / 60.0, 2.0), 7.0)
            workorder.write({'date_start': cursor, 'date_finished': cursor + timedelta(hours=hours)})
            first = first or cursor
            cursor = _work(cursor + timedelta(hours=hours), rnd)
        if first:
            production.write({'date_start': first, 'date_finished': production.workorder_ids.sorted('id')[-1].date_finished})
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
            _backdate(env, 'stock_lot', lot, _work(job.create_date + timedelta(hours=rnd.randint(1, 5), minutes=rnd.randint(0, 59)), rnd))
    # deadlines against the planned finish: most orders fit, two do not (one already late, one will be late)
    open_productions = env['mrp.production'].search([('state', 'in', ('confirmed', 'progress', 'to_close'))])
    for production in open_productions:
        sale = production.sudo().reference_ids.sale_ids[:1]
        base = sale.date_order or now
        finish = production.date_finished or now
        production.date_deadline = now + timedelta(days=rnd.randint(3, 20) if production.state == 'confirmed' else rnd.randint(2, 9))
    late.date_deadline = now - timedelta(days=2)
    open_productions.filtered(lambda p: p.state == 'confirmed')[-1:].date_deadline = now - timedelta(days=1)
    waiting[:1].date_deadline = now + timedelta(days=2)  # the one that will not make it: the deadline is close, the plan is longer
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
    # section load: the working calendar of each section (standard resource.calendar) gives the hours the section has for
    # these orders in a week; they are set so that the show has a believable picture (one bottleneck). The calendars are
    # given after the work orders are planned, so the dates of the order book do not change.
    for code, percent in {'CUT': 74, 'EDG': 97, 'DRL': 83, 'ASM': 118}.items():
        center = env['mrp.workcenter'].search([('code', '=', code)], limit=1)
        hours = center.workcenter_load / 60.0 if center else 0.0
        if center and hours:
            weekly = max(1, round(hours / percent * 100.0))
            # more than one shift of 40 h: parallel places of the section (standard capacity without a product)
            parallel = max(1, math.ceil(weekly / 40.0))
            if parallel > 1:
                center.capacity_ids = [(5, 0, 0), (0, 0, {'product_uom_id': env.ref('uom.product_uom_unit').id,
                                                          'capacity': parallel})]
            center.resource_calendar_id = _section_calendar(env, center, round(weekly / parallel, 1))
    show = seed_dates(env, people, partners, rnd, install)
    full_state = seed_full(env, people, partners, orders, show, rnd)
    _age_system_messages(env)
    # no chatter message dated «yesterday»: the web client shows that word untranslated, a plain date reads better
    env.cr.execute("""UPDATE mail_message SET date = date - interval '1 day' WHERE date >= (date_trunc('day', now() at time zone 'Europe/Kyiv') - interval '1 day') at time zone 'Europe/Kyiv'
                      AND date < date_trunc('day', now() at time zone 'Europe/Kyiv') at time zone 'Europe/Kyiv'""")
    env.cr.execute("UPDATE mail_notification SET is_read = true, read_date = now() WHERE is_read IS NOT TRUE")  # no «94 unread» badge in the header
    # wave 2: the letters to the customers and the morning briefing of the owner come after, new (F-51, F-64)
    from .wave2 import seed_wave2_after
    seed_wave2_after(env, people, dict(full_state.get('wave2', {}), show=show.id))
    env.flush_all()
    return {'orders': env['sale.order'].search_count([]), 'productions': env['mrp.production'].search_count([])}
