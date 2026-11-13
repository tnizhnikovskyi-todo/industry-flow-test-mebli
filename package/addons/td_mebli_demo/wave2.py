"""Demo data of the wave 2 positions of the A box (flow/decisions.md, records 42-47): F-50...F-65.

Fictional data only. Called at the end of seed_full (before the chatter is aged) and, for the briefing, at the very end
of seed_showcase (after the notifications are marked read, so the owner finds it unread in the inbox)."""
import base64
import io
import json
from datetime import datetime, time, timedelta

import pytz

from odoo import fields

TZ = pytz.timezone('Europe/Kyiv')
# supplier history (F-63): days late of the earlier receipts; the painter keeps his dates, the stone shop is late
HISTORY = {'fronts_9010': (0, [0, 0, -1]), 'worktop_quartz': (1, [4, 6, 5, 7]), 'profile_champagne': (2, [1, 2])}


def _utc(day, hour, minute=0):
    return TZ.localize(datetime.combine(day, time(hour, minute))).astimezone(pytz.utc).replace(tzinfo=None)


def _workdays(start, end):
    day = start
    while day <= end:
        if day.weekday() < 5:
            yield day
        day += timedelta(days=1)


def _supplier_history(env, rnd):
    """F-63: the history of receipts of the suppliers. The earlier price history (td_mebli_purchase) is received on the
    day of the seed: its receipt dates are put back next to the expected arrival (0-2 days late), and the suppliers of
    the made-to-order items get a history of their own."""
    from .dates import COMPONENTS, SUPPLIERS, _receive
    env.flush_all()
    env.cr.execute("""
        SELECT m.id, pol.date_planned FROM stock_move m JOIN purchase_order_line pol ON pol.id = m.purchase_line_id
         WHERE m.state = 'done' AND m.date > pol.date_planned + interval '3 days'""")
    for move_id, planned in env.cr.fetchall():
        when = planned + timedelta(days=rnd.choice([0, 0, 1, 2]), hours=rnd.randint(1, 5))
        env.cr.execute('UPDATE stock_move SET date = %s WHERE id = %s', (when, move_id))
        env.cr.execute('UPDATE stock_move_line SET date = %s WHERE move_id = %s', (when, move_id))
    env.cr.execute("""UPDATE stock_picking p SET date_done = sub.d FROM (
                        SELECT picking_id, max(date) d FROM stock_move WHERE state = 'done' AND picking_id IS NOT NULL
                         AND purchase_line_id IS NOT NULL GROUP BY picking_id) sub WHERE sub.picking_id = p.id""")
    env.invalidate_all()
    names = {key: name for key, name, *_rest in COMPONENTS}
    now = fields.Datetime.now()
    for key, (supplier_index, delays) in HISTORY.items():
        product = env['product.product'].search([('name', '=', names[key])], limit=1)
        supplier = env['res.partner'].search([('name', '=', SUPPLIERS[supplier_index][0])], limit=1)
        if not product or not supplier:
            continue
        for position, late in enumerate(delays):
            ordered = now - timedelta(days=150 - position * 35, hours=rnd.randint(1, 5))
            planned = ordered + timedelta(days=product.seller_ids[:1].delay or 10)
            order = env['purchase.order'].create({'partner_id': supplier.id, 'user_id': False, 'order_line': [(0, 0, {
                'product_id': product.id, 'product_qty': 2.0, 'price_unit': product.standard_price, 'date_planned': planned})]})
            order.button_confirm()
            order.write({'date_order': ordered, 'date_approve': ordered})
            for picking in order.picking_ids:
                _receive(picking)
            env.flush_all()
            when = planned + timedelta(days=late, hours=rnd.randint(1, 4))
            for move in order.order_line.move_ids:
                env.cr.execute('UPDATE stock_move SET date = %s WHERE id = %s', (when, move.id))
                env.cr.execute('UPDATE stock_move_line SET date = %s WHERE move_id = %s', (when, move.id))
            env.cr.execute('UPDATE stock_picking SET date_done = %s WHERE id IN %s', (when, tuple(order.picking_ids.ids)))
            env.cr.execute('UPDATE purchase_order SET create_date = %s WHERE id = %s', (ordered, order.id))
            env.invalidate_all()


def _measure_rules(env, show):
    """F-62: the hall niche has a ventilation duct; the wardrobe of the order is placed into it."""
    sheet = show.td_measure_ids[:1]
    niche = sheet.niche_ids.filtered(lambda n: n.name.startswith('Шафа-купе'))[:1]
    line = show.order_line.filtered(lambda l: l.product_id.product_tmpl_id == env.ref('td_mebli_demo.prod_wardrobe'))[:1]
    if niche and line:
        niche.write({'protrusion_mm': 40, 'order_line_id': line.id})
    return sheet


def _design_visual(env, show):
    """F-53: a visual of the designer for the quotation — a simple elevation drawn here (the real one comes from the
    design program of the salon)."""
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (1400, 760), (246, 244, 240))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 640, 1400, 760], fill=(214, 206, 194))            # floor
    draw.rectangle([80, 120, 1000, 210], fill=(250, 250, 248), outline=(150, 150, 150), width=3)  # wall cabinets
    for x in range(80, 1000, 153):
        draw.rectangle([x, 120, x + 153, 210], outline=(170, 170, 170), width=2)
    draw.rectangle([80, 380, 1000, 400], fill=(92, 92, 96))              # quartz worktop
    draw.rectangle([80, 400, 1000, 640], fill=(250, 250, 248), outline=(150, 150, 150), width=3)  # base cabinets
    for x in range(80, 1000, 153):
        draw.rectangle([x, 400, x + 153, 640], outline=(170, 170, 170), width=2)
        draw.rectangle([x + 60, 420, x + 92, 426], fill=(120, 120, 120))
    draw.rectangle([1010, 60, 1300, 640], fill=(250, 250, 248), outline=(150, 150, 150), width=3)  # tall unit
    draw.rectangle([1150, 330, 1156, 400], fill=(120, 120, 120))
    draw.rectangle([400, 230, 700, 370], fill=(232, 228, 220), outline=(200, 196, 188))           # backsplash
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    show.td_design_image = base64.b64encode(buffer.getvalue())


def _booking(env, people, rnd):
    """F-54: the calendar of the measurer — booked measurements in the next days and an opportunity to book."""
    measurer = people['measure']
    today = fields.Date.context_today(measurer)
    Partner = env['res.partner']
    leads = env['crm.lead'].search([('name', 'in', ('Шафа в нішу, будинок', 'Кухня, новобудова', 'Гардероб, квартира'))])
    for index, lead in enumerate(leads):
        if not lead.partner_id:
            lead.partner_id = Partner.create({'name': lead.contact_name, 'lang': 'uk_UA', 'city': 'Київ',
                                              'phone': f'+380 00 000 03 {index + 1:02d}',
                                              'email': f'client{index + 31}@customer-demo.example'})
    alarm = env.ref('td_mebli_measure.alarm_mail_measure_1day')
    slots = [(1, 10), (1, 14), (2, 9), (3, 12), (3, 16), (4, 10)]
    customers = [('Ірина Шевчук', 'Ірпінь'), ('Максим Павленко', 'Київ'), ('Олена Мороз', 'Бровари'),
                 ('Тарас Гнатюк', 'Київ'), ('Наталія Бойко', 'Вишневе'), ('Дмитро Лисенко', 'Київ')]
    events = env['calendar.event']
    for index, ((days, hour), (name, city)) in enumerate(zip(slots, customers)):
        day = today + timedelta(days=days)
        while day.weekday() >= 5:
            day += timedelta(days=1)
        partner = Partner.create({'name': name, 'lang': 'uk_UA', 'city': city, 'phone': f'+380 00 000 04 {index + 1:02d}',
                                  'email': f'client{index + 41}@customer-demo.example'})
        lead = env['crm.lead'].create({'name': f'Кухня, {city}' if index % 2 == 0 else f'Шафа-купе, {city}',
                                       'type': 'opportunity', 'partner_id': partner.id, 'user_id': people['salon'].id})
        events |= env['calendar.event'].with_context(no_mail_to_attendees=True).create({
            'name': f'Замір: {name}', 'start': _utc(day, hour), 'stop': _utc(day, hour + 2),
            'user_id': measurer.id, 'partner_ids': [(6, 0, (measurer.partner_id | partner).ids)],
            'opportunity_id': lead.id, 'alarm_ids': [(6, 0, alarm.ids)], 'location': city})
    return leads.filtered(lambda l: l.name == 'Кухня, новобудова')[:1] or leads[:1]


def _paid_repair(env, people, orders, rnd):
    """F-55: a claim after the warranty — the customer pays: the standard quotation of the repair, then the invoice."""
    now = fields.Datetime.now()
    order = orders['done'].sorted('date_order')[:1]
    if not order:
        return env['repair.order']
    old = now - timedelta(days=800)  # delivered more than two years ago (the warranty of the package — 24 months)
    env.flush_all()
    env.cr.execute('UPDATE stock_picking SET date_done = %s WHERE sale_id = %s AND state = %s', (old, order.id, 'done'))
    env.cr.execute('UPDATE sale_order SET effective_date = %s, date_order = %s WHERE id = %s',
                   (old, old - timedelta(days=30), order.id))
    env.invalidate_all()
    line = order.order_line.filtered('td_bom_id')[:1]
    tag = env['repair.tags'].search([('name', '=', 'Клієнт')], limit=1)
    hinge = env.ref('td_mebli_demo.fit_hinge')
    repair = env['repair.order'].create({
        'partner_id': order.partner_id.id, 'product_id': line.product_id.id, 'td_claim_order_id': order.id,
        'tag_ids': [(6, 0, tag.ids)], 'user_id': people['chief'].id, 'schedule_date': now + timedelta(days=4),
        'internal_notes': '<p>Провисла дверка навісної шафи, зламана петля. Гарантія закінчилась — ремонт платний.</p>',
        'move_ids': [(0, 0, {'product_id': hinge.id, 'product_uom_qty': 2.0, 'repair_line_type': 'add'})],
    })
    repair.action_validate()
    if repair.state == 'draft':
        repair._action_repair_confirm()
    repair.action_create_sale_order()
    sale = repair.sale_order_id
    service = env['product.product'].search([('default_code', '=', 'ВИЇЗД')], limit=1) or env['product.product'].create({
        'name': 'Виїзд майстра й ремонт', 'type': 'service', 'list_price': 650.0, 'default_code': 'ВИЇЗД',
        'sale_ok': True, 'purchase_ok': False, 'invoice_policy': 'order'})
    sale.order_line = [(0, 0, {'product_id': service.id, 'product_uom_qty': 1.0})]
    sale.user_id = people['salon']
    sale.action_confirm()
    try:
        invoice = sale._create_invoices()
        invoice.action_post()
    except Exception:  # noqa: BLE001 — the quotation alone shows the paid repair
        pass
    return repair


def _maintenance(env, people, rnd):
    """F-60: the machines of the sections, planned maintenance and a breakdown with downtime yesterday."""
    now = fields.Datetime.now()
    today = fields.Date.context_today(people['chief'])
    centers = {c.code: c for c in env['mrp.workcenter'].search([])}
    machines = {}
    for code, name, serial in (('CUT', 'Форматно-розкрійний верстат', 'ФР-3200'),
                               ('EDG', 'Кромкооблицювальний верстат', 'КО-450'),
                               ('DRL', 'Свердлильно-присадний верстат', 'СП-21')):
        if code in centers:
            machines[code] = env['maintenance.equipment'].create({
                'name': name, 'serial_no': serial, 'td_workcenter_id': centers[code].id,
                'technician_user_id': people['chief'].id, 'effective_date': today - timedelta(days=900)})
    Request = env['maintenance.request']
    stages = env['maintenance.stage'].search([], order='sequence')
    done_stage = stages.filtered('done')[:1]
    for code, machine in machines.items():
        Request.create({'name': f'Планове ТО: {machine.name}', 'equipment_id': machine.id, 'maintenance_type': 'preventive',
                        'schedule_date': _utc(today + timedelta(days=rnd.randint(5, 20)), 14), 'duration': 3.0,
                        'repeat_interval': 1, 'repeat_unit': 'month', 'repeat_type': 'forever',
                        'user_id': people['chief'].id})
    breakdown = env['maintenance.request']
    edge = machines.get('EDG')
    if edge:
        yesterday = today - timedelta(days=1)
        while yesterday.weekday() >= 5:
            yesterday -= timedelta(days=1)
        breakdown = Request.create({'name': 'Не прижимає кромку, перегрів клейового вузла', 'equipment_id': edge.id,
                                    'maintenance_type': 'corrective', 'user_id': people['chief'].id,
                                    'request_date': yesterday, 'priority': '2'})
        breakdown.action_td_start_downtime()
        breakdown.td_downtime_id.write({'date_start': _utc(yesterday, 10, 15), 'date_end': _utc(yesterday, 12, 45),
                                        'description': breakdown.name})
        if len(stages) > 1:
            breakdown.stage_id = stages[1]
    if done_stage and machines.get('CUT'):
        old = Request.create({'name': 'Заміна пиляльного диска', 'equipment_id': machines['CUT'].id,
                              'maintenance_type': 'corrective', 'user_id': people['chief'].id,
                              'request_date': today - timedelta(days=12)})
        old.stage_id = done_stage
    return breakdown


def _attendance(env, rnd):
    """F-61: the kiosk with a PIN (standard Attendances) and the time of the shop floor this month."""
    company = env.company
    company.write({'attendance_kiosk_mode': 'manual', 'attendance_kiosk_use_pin': True})
    # the employee of the administrator is in the kiosk list: a Ukrainian name in the frame
    env['hr.employee'].search([('user_id', '=', env.ref('base.user_admin').id)]).write({'name': 'Адміністратор системи'})
    today = fields.Date.context_today(env['res.users'].browse(env.uid))
    start = today.replace(day=1)
    workers = env['hr.employee'].search([('pin', '!=', False), ('user_id', '=', False)])
    Attendance = env['hr.attendance'].sudo()
    for employee in workers:
        for day in _workdays(start, today - timedelta(days=1)):
            if rnd.random() < 0.05:
                continue  # a day off or sick
            check_in = _utc(day, 8, rnd.randint(0, 12))
            check_out = _utc(day, 17, rnd.randint(0, 25))
            Attendance.create({'employee_id': employee.id, 'check_in': check_in, 'check_out': check_out})
        if today.weekday() < 5:
            Attendance.create({'employee_id': employee.id, 'check_in': _utc(today, 8, rnd.randint(0, 10))})


def _analogs(env):
    """F-57 (box B): analogs of the materials. The sliding system of the wardrobes ran out (the free sets went to other
    orders): one waiting order is short of it and the analog of another producer, in stock, is suggested."""
    from .hooks import _add_stock
    slide = env.ref('td_mebli_demo.fit_slide')
    analog = env['product.product'].create({
        'name': 'Розсувна система РС-2М (інший виробник)', 'type': 'consu', 'is_storable': True,
        'uom_id': slide.uom_id.id, 'standard_price': round(slide.standard_price * 0.97, 2), 'purchase_ok': True,
        'sale_ok': False, 'td_material_kind': slide.td_material_kind, 'default_code': 'ФР-РС2М'})
    slide.product_tmpl_id.td_analog_ids = [(6, 0, analog.ids)]
    location = env['stock.warehouse'].search([('company_id', '=', env.company.id)], limit=1).lot_stock_id
    _add_stock(env, location, analog, 12.0)
    # not the order of the show (S00123): its manufacturing orders are on the screens of scenes 2 and 5
    production = env['stock.move'].search([('raw_material_production_id.state', '=', 'confirmed'),
                                           ('raw_material_production_id.origin', 'not ilike', 'S00123'),
                                           ('product_id', '=', slide.id)], order='id desc', limit=1).raw_material_production_id
    if production:
        production.move_raw_ids.filtered(lambda m: m.product_id == slide)._do_unreserve()
        quants = env['stock.quant'].search([('product_id', '=', slide.id), ('location_id.usage', '=', 'internal')])
        for quant in quants:
            quant.inventory_quantity = quant.reserved_quantity
        quants.action_apply_inventory()
    return analog, production


def _vendor_prices(env):
    """F-59: the boards already have prices of the distributor in the vendor pricelist (the import updates them)."""
    from .full import MATERIAL_SUPPLIERS
    vendor = env['res.partner'].search([('name', '=', MATERIAL_SUPPLIERS[0][0])], limit=1)
    for xmlid, price in (('board_sonoma', 489.0), ('board_white', 455.0)):
        product = env.ref(f'td_mebli_demo.{xmlid}')
        env['product.supplierinfo'].create({'partner_id': vendor.id, 'product_tmpl_id': product.product_tmpl_id.id,
                                            'price': price, 'delay': 3, 'product_code': product.default_code})


def _consumption(env):
    """F-52: the order BoMs warn about overconsumption (standard «Allowed with warning»): one order in progress used more
    edge banding than planned."""
    production = env['mrp.production'].search([('state', 'in', ('progress', 'to_close')), ('bom_id.td_order_bom', '=', True)],
                                              order='id desc', limit=1)
    for move in production.move_raw_ids.filtered(lambda m: m.has_tracking == 'none' and m.product_uom_qty
                                                 and m.product_id.td_material_kind == 'edge')[:1]:
        move.quantity = round(move.product_uom_qty * 1.18, 2)
        move.picked = True
    return production


def seed_wave2(env, people, orders, show, rnd):
    import random
    rnd = random.Random(2027)  # an own sequence: the data of the earlier waves stays as it was
    _supplier_history(env, rnd)
    sheet = _measure_rules(env, show)
    _design_visual(env, show)
    lead = _booking(env, people, rnd)
    repair = _paid_repair(env, people, orders, rnd)
    breakdown = _maintenance(env, people, rnd)
    _attendance(env, rnd)
    analog, analog_mo = _analogs(env)
    _vendor_prices(env)
    consumption = _consumption(env)
    env.flush_all()
    env['sale.order'].with_context(td_no_forecast_activity=False)._cron_td_forecast_activity()
    return {'measure_sheet': sheet.id, 'booking_lead': lead.id, 'paid_repair': repair.id, 'breakdown': breakdown.id,
            'analog': analog.id, 'analog_mo': analog_mo.id, 'consumption_mo': consumption.id}


def seed_wave2_after(env, people, ids):
    """At the very end: the letters to the customers and the morning briefing (new, unread), the ids for the shots."""
    owner = people['owner']
    owner.notification_type = 'inbox'
    # the factory works in Kyiv: the server-side dates of the reports, letters and the shop board in local time
    env['res.users'].search([('share', '=', False)]).write({'tz': 'Europe/Kyiv'})
    env.company.resource_calendar_id.tz = 'Europe/Kyiv'  # the working hours of the factory (day plan, shop board)
    channel = env.ref('mail.channel_all_employees', raise_if_not_found=False)
    if channel:
        channel.name = 'Загальний'  # the standard channel of the employees: a Ukrainian name in the frame
    # rights of the demo roles for the new screens: the finance manager makes the time sheet, the production manager
    # leads the maintenance of the machines
    people['fin'].group_ids = [(4, env.ref('hr_attendance.group_hr_attendance_manager').id)]
    people['chief'].group_ids = [(4, env.ref('maintenance.group_equipment_manager').id)]
    # the PDF of the shots: wkhtmltopdf reads the styles from the show server (README §5, «PDF»)
    import os
    env['ir.config_parameter'].sudo().set_param('report.url', os.environ.get('DEMO_REPORT_URL', 'http://127.0.0.1:8072'))
    reminders = env['project.task']._cron_td_customer_reminders()
    env['res.partner']._cron_td_morning_briefing()
    from .dates import SUPPLIERS
    payment = env.ref('td_mebli_notify.mail_template_td_payment_reminder')
    letter = env['mail.message'].search([('model', '=', 'sale.order'), ('subtype_id', '=', env.ref('mail.mt_comment').id),
                                         ('subject', 'ilike', '%')], order='id desc').filtered(
        lambda m: m.subject == payment._render_field('subject', [m.res_id])[m.res_id])[:1]
    picking = env['stock.picking'].search([('picking_type_code', '=', 'outgoing'), ('state', '=', 'done'),
                                           ('sale_id', '!=', False)], order='date_done desc', limit=1)
    fitter = people['fitter']
    visits = env['project.task'].search([('user_ids', 'in', fitter.ids), ('sale_order_id', '!=', False),
                                         ('state', 'not in', ('1_done', '1_canceled')),
                                         ('date_deadline', '>=', _utc(fields.Date.context_today(fitter), 0))],
                                        order='date_deadline')
    day_plan = visits  # the day plan prints a page per day: today and the next visits of the crew
    ids = dict(ids, reminders=reminders,
               stone_supplier=env['res.partner'].search([('name', '=', SUPPLIERS[1][0])], limit=1).id,
               payment_letter_order=letter.res_id or 0, handover_picking=picking.id,
               day_plan_tasks=','.join(str(i) for i in day_plan.ids) or '0', fitter_user=fitter.id,
               kiosk_key=env.company.attendance_kiosk_key)
    # the records of the A1-A4 shots (the same as in the earlier shoot: the seed is deterministic)
    order = lambda name: env['sale.order'].search([('name', '=', name)], limit=1)  # noqa: E731
    job = env['td.mebli.cutting.job'].search([('purchase_id', '!=', False)], limit=1)
    nopay = order('S00102')
    ids.update(nopay_order=nopay.id, paid_order=order('S00098').id, kit_order=order('S00009').id,
               cut_order=job.production_ids.sudo().reference_ids.sale_ids[:1].id, cut_job=job.id,
               nopay_task=env['project.task'].search([('sale_order_id', '=', nopay.id)], order='date_deadline', limit=1).id,
               act=env['td.mebli.install.act'].search([('name', '=', 'АКТ-0002')], limit=1).id)
    env['ir.config_parameter'].sudo().set_param('td_mebli_demo.shot_ids', json.dumps(ids))
    return ids
