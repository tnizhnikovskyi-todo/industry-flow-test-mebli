"""Full scope of the slice (A-21, wave 1): data for all scenes of SALES §6 and the cards of the manager dashboard.

seed_full(...) runs at the end of seed_showcase, after seed_dates (the show order S-02). Everything is fictional: people,
suppliers, sizes and prices are invented; phones +380 00 000 00 NN, mail only on *.example domains.
What is standard stays standard: visits are project tasks created by the installation service line of the order
(sale_project), claims are repair orders, purchases and receipts are Purchase/Inventory documents, time is the standard
time line of the work order. The td_ records are only those the standard has no place for (measurement sheet, act,
quality check, packing list, accrual, order change).
"""
import base64
import math
from datetime import timedelta

from odoo import fields
from odoo.tools import file_open

# shop workers and installers: name, job, work center code (None: crew), hourly cost UAH, PIN (demo only)
WORKERS = [
    ('Петро Гуменюк', 'Оператор розкрою', 'CUT', 165.0, '1111'),
    ('Василь Ткач', 'Оператор кромкування', 'EDG', 155.0, '2222'),
    ('Оксана Литвин', 'Оператор присадки', 'DRL', 150.0, '3333'),
    ('Сергій Бондаренко', 'Складальник', 'ASM', 160.0, '4444'),
    ('Іван Кушнір', 'Монтажник', None, 170.0, '5555'),
    # the assembly section has four assemblers: one assembler for all the orders gave an implausible monthly piecework
    ('Андрій Мельник', 'Складальник', 'ASM', 160.0, '7777'),
    ('Юрій Савчук', 'Складальник', 'ASM', 160.0, '8888'),
    ('Роман Ковальчук', 'Складальник', 'ASM', 160.0, '9999'),
    # the second cutter: the tablet allows one running timer per worker (review of the Architect, round 1), the
    # scenes take two cutting work orders in a row (screen 5 and the clip D_tablet)
    ('Олег Дорошенко', 'Оператор розкрою', 'CUT', 165.0, '1212'),
]
# crew share of the order amount (without taxes) for the installation, in the demo (a parameter of the act; calibrated
# so that one crew of two installers gets a believable month: about 15-30 thousand UAH each; the demo factory installs
# about 60 orders a month with one crew, so the share is lower than a crew of a smaller factory would get)
CREW_PCT = 2.0
QUALITY_POINT = 'Кромка без сколів і щілин, фото торця'
INSTALL_PRODUCT = 'Доставка й монтаж (у вартості замовлення)'

# fictional suppliers of the standard materials and the prices of their earlier purchases (UAH per unit of the product)
MATERIAL_SUPPLIERS = [('Плита-Трейд', 'Київ'), ('Фурнітура Плюс', 'Львів')]
PRICE_HISTORY = {  # product xmlid: (supplier index, base price, quantity per purchase)
    'edge_white_2': (0, 12.5, 400), 'edge_sonoma_2': (0, 14.0, 400), 'fit_legs': (1, 24.0, 200),
    'fit_hinge': (1, 62.0, 300), 'fit_slide': (1, 3300.0, 6), 'fit_guide': (1, 190.0, 120),
}
PRICE_JUMP = {'fit_hinge': 1.11, 'fit_slide': 1.08}  # this month: the fittings supplier raised the prices

SPEC_NICHES = [('Ніша під холодильник (пенал)', 600, 2100, 560), ('Ніша під духову шафу', 600, 600, 560),
               ('Ніша під посудомийку', 600, 820, 560), ('Шафа-купе в передпокої', 1800, 2400, 600)]
SPEC_APPLIANCES = [('Холодильник, вбудований', 0, 595, 2010, 590), ('Духова шафа', 1, 595, 595, 550),
                   ('Посудомийна машина', 2, 598, 815, 550)]


def _image(name):
    with file_open('td_mebli_demo/static/img/' + name, 'rb') as handle:
        return base64.b64encode(handle.read())


def _photos(env, record, photos):
    """Photo stubs (product pictures of the demo, not real photos) attached to a measurement sheet or an act."""
    attachments = env['ir.attachment'].create([
        {'name': name, 'datas': _image(image), 'mimetype': 'image/png', 'res_model': record._name, 'res_id': record.id}
        for name, image in photos])
    record.photo_ids = [(6, 0, attachments.ids)]


def _employees(env, people):
    """Standard employees with a PIN and an hourly cost (hr, hr_hourly_cost); the installer is the user of the crew."""
    Employee = env['hr.employee'].sudo()
    by_center, team, crew = {}, {}, Employee
    for index, (name, job, code, cost, pin) in enumerate(WORKERS, start=1):
        vals = {'name': name, 'job_title': job, 'hourly_cost': cost, 'pin': pin,
                'work_phone': f'+380 00 000 01 {index:02d}', 'work_email': f'worker{index}@demo-fabryka.example'}
        if code is None:
            vals['user_id'] = people['fitter2'].id
        employee = Employee.create(vals)
        if code:
            by_center.setdefault(code, employee)
            team[code] = team.get(code, Employee) | employee
        else:
            crew |= employee
    crew |= Employee.create({'name': people['fitter'].name, 'job_title': 'Бригадир монтажників', 'hourly_cost': 190.0,
                             'user_id': people['fitter'].id, 'pin': '6666', 'work_email': 'fitter@demo-fabryka.example'})
    return by_center, team, crew


def _shop_history(env, by_center, team, rnd):
    """The time lines written by the tablet so far get the worker who confirmed them; the edge banding has a quality step."""
    for operation in env['mrp.routing.workcenter'].search([('workcenter_id.code', '=', 'EDG')]):
        operation.td_quality_point = QUALITY_POINT
    lines = env['mrp.workcenter.productivity'].search([('workorder_id', '!=', False)])
    for code, employees in team.items():
        # one worker per work order; a section with several workers shares its work orders evenly by the piecework
        # (the largest work order goes to the worker with the least work so far)
        by_order = lines.filtered(lambda line: line.workcenter_id.code == code).grouped('workorder_id')
        load = {employee: 0.0 for employee in employees}

        def _piece(workorder):
            operation = workorder.operation_id
            return operation.td_piece_rate * operation._td_basis_quantity() * (workorder.qty_produced or 1.0) if operation else 0.0
        for workorder, wo_lines in sorted(by_order.items(), key=lambda item: (-_piece(item[0]), item[0].id)):
            employee = min(employees, key=lambda e: (load[e], e.id))
            load[employee] += _piece(workorder)
            wo_lines.write({'td_employee_id': employee.id})
    # one running timer per worker (the tablet refuses a second one, review of the Architect, round 1): the earlier
    # work orders of a worker are paused (the line ends where his next one starts); the cutters are free for scene 5
    now = fields.Datetime.now()
    running = lines.filtered(lambda line: not line.date_end and line.loss_type == 'productive' and line.td_employee_id)
    for employee, emp_lines in running.grouped('td_employee_id').items():
        ordered = emp_lines.sorted(lambda line: (line.date_start, line.id))
        to_close = ordered if employee in team.get('CUT', ()) else ordered[:-1]
        for index, line in enumerate(to_close):
            following = ordered[index + 1].date_start if index + 1 < len(ordered) else None
            end = following if following and following > line.date_start else line.date_start + timedelta(minutes=45)
            line.date_end = min(end, now)
    photo = _image('prod_kitchen.png')
    since = fields.Datetime.now() - timedelta(days=30)
    edge_done = env['mrp.workorder'].search([('workcenter_id.code', '=', 'EDG'), ('state', '=', 'done'),
                                             ('date_finished', '>=', since)])
    Check = env['td.mebli.quality.check']
    for index, workorder in enumerate(edge_done):
        if index == 3:  # one chip found and redone: the record stays
            Check.create({'workorder_id': workorder.id, 'name': QUALITY_POINT, 'result': 'fail', 'photo': photo,
                          'note': 'Скол кромки на торці фасаду, переклеєно', 'employee_id': by_center['EDG'].id})
        Check.create({'workorder_id': workorder.id, 'name': QUALITY_POINT, 'result': 'pass', 'photo': photo,
                      'employee_id': by_center['EDG'].id})


def _installation_project(env):
    """Called before the orders: the installation service line of every order makes the visit task (sale_project)."""
    project = env['project.project'].create({'name': 'Монтажі', 'allow_billable': True,
                                             'privacy_visibility': 'employees'})
    product = env['product.product'].create({
        'name': INSTALL_PRODUCT, 'type': 'service', 'list_price': 0.0, 'standard_price': 0.0,
        'invoice_policy': 'delivery', 'service_type': 'manual', 'service_tracking': 'task_global_project',
        'project_id': project.id, 'sale_ok': True, 'purchase_ok': False, 'default_code': 'МОНТАЖ'})
    return project, product


def _visit(task, when, crew_user):
    task.write({'date_deadline': when, 'user_ids': [(6, 0, crew_user.ids)]})


def _finish(production, end, rnd):
    """Finish the open work orders with believable times ending at `end`, then the manufacturing order."""
    todo = production.workorder_ids.filtered(lambda w: w.state not in ('done', 'cancel')).sorted('id', reverse=True)
    for workorder in todo:
        workorder.button_start()
        workorder.button_finish()
        minutes = (workorder.duration_expected or 60.0) * rnd.uniform(0.92, 1.1)
        just_closed = fields.Datetime.now() - timedelta(minutes=5)
        workorder.time_ids.filtered(lambda t: t.date_end and t.date_end >= just_closed).write(
            {'date_start': end - timedelta(minutes=minutes), 'date_end': end})
        workorder.write({'date_start': end - timedelta(minutes=minutes), 'date_finished': end})
        end -= timedelta(minutes=minutes + rnd.randint(20, 60))
    production.with_context(skip_consumption=True, skip_backorder=True).button_mark_done()


def _installations(env, people, orders, crew, rnd):
    """Visits and acts: finished orders installed with a signed final act; open visits on the calendar."""
    from .showcase import _deliver, _work, _past, _note
    now = fields.Datetime.now()
    since = now - timedelta(days=30)
    fitter, fitter2 = people['fitter'], people['fitter2']
    crew_users = fitter | fitter2
    Act = env['td.mebli.install.act']
    photo = _image('prod_kitchen.png')
    on_time_misses = 0
    acts = Act
    for task in env['project.task'].search([('sale_order_id', '!=', False)]):
        task.name = f'{task.sale_order_id.name}: монтаж'  # not the name of the service line
    for order in orders['done'].sorted('date_order'):
        task = order.tasks_ids[:1]
        # the planned finish of the manufacturing orders can lie in the future: the installation then falls on one of the
        # last working days (not all on today, which piled the installations of a month into one day)
        finished = min(max(order.mrp_production_ids.mapped('date_finished') or [order.date_order]),
                       order.date_order + timedelta(days=rnd.randint(12, 18)))
        target = finished + timedelta(days=rnd.randint(1, 3))
        if target > now - timedelta(hours=2):
            target = now - timedelta(days=rnd.randint(1, 9), hours=rnd.randint(0, 6))
        visit = _past(_work(target, rnd), now, rnd)
        _visit(task, visit, crew_users)
        late = finished >= since and on_time_misses < 2 and rnd.random() < 0.12
        on_time_misses += late
        promised = visit - timedelta(days=rnd.randint(2, 4)) if late else visit + timedelta(days=rnd.randint(0, 4))
        order.commitment_date = fields.Datetime.to_datetime(fields.Date.to_date(promised)) + timedelta(hours=15)
        if visit < since:
            task.state = '1_done'
            continue
        act = Act.with_user(fitter).create({'task_id': task.id, 'kind': 'final', 'crew_pct': CREW_PCT,
                                            'signed_by': order.partner_id.name, 'signature': photo,
                                            'photo_ids': [], 'photo_archive': rnd.random() < 0.3})
        act.with_user(fitter).action_sign()
        acts |= act
        env.flush_all()  # the signing date is written by the ORM: flush it before the back-dating, or it overwrites it
        env.cr.execute('UPDATE td_mebli_install_act SET signed_on = %s, create_date = %s WHERE id = %s',
                       (visit + timedelta(hours=3), visit, act.id))
    acts.invalidate_recordset(['signed_on', 'create_date'])
    # two acts with defects (one already fixed)
    for act, (text, resolved) in zip(acts[:2], (('Зазор лівої дверки 3 мм, відрегулювати', False),
                                                  ('Подряпина на цоколі, замінено', True))):
        act.defect_ids = [(0, 0, {'name': text, 'resolved': resolved, 'photo': photo})]
        _note(act, fitter, 'Клієнт підписав акт, недолік записано, виїзд на регулювання — за домовленістю.', act.signed_on)
        _photos(env, act, [('Кухня після монтажу.png', 'prod_kitchen.png'), ('Недолік: дверка.png', 'prod_wardrobe.png')])
    # orders in progress: two installed but not fully paid (prepayment only), one ready and not shipped, one to install now
    progress = orders['progress'].sorted('date_order')
    paid_late, ready, to_sign = progress[:2], progress[2:3], progress[3:4]
    for order in paid_late | ready | to_sign:
        for production in order.mrp_production_ids.filtered(lambda p: p.state not in ('done', 'cancel')):
            end = _past(now - timedelta(days=rnd.randint(1, 3)), now, rnd)
            _finish(production, end, rnd)
            production.date_finished = end
        order.action_td_build_kit()
    for order in paid_late | to_sign:
        order.td_kit_line_ids.write({'packed': True, 'packed_by_id': people['store'].id})
        _deliver(order)
    for order in paid_late:
        task = order.tasks_ids[:1]
        visit = _past(now - timedelta(days=1, hours=rnd.randint(0, 4)), now, rnd)
        _visit(task, visit, crew_users)
        order.commitment_date = fields.Datetime.to_datetime(fields.Date.to_date(visit + timedelta(days=2))) + timedelta(hours=15)
        act = Act.with_user(fitter).create({'task_id': task.id, 'kind': 'final', 'signed_by': order.partner_id.name,
                                            'signature': photo, 'photo_archive': True, 'crew_pct': CREW_PCT})
        act.with_user(fitter).action_sign()
        env.flush_all()
        env.cr.execute('UPDATE td_mebli_install_act SET signed_on = %s WHERE id = %s', (visit + timedelta(hours=3), act.id))
        act.invalidate_recordset(['signed_on'])
    # ready: the back panels of the wardrobe/dresser are not packed yet — the delivery is blocked (scene 5)
    missing = ready.td_kit_line_ids.filtered(lambda line: 'Задня стінка' in line.item)
    (ready.td_kit_line_ids - missing).write({'packed': True, 'packed_by_id': people['store'].id})
    # to sign now: the visit is today, the act is a draft the installer completes on the phone (scene 6)
    for order in to_sign:
        task = order.tasks_ids[:1]
        _visit(task, _work(now.replace(hour=7, minute=0), rnd), crew_users)
        order.commitment_date = now + timedelta(days=1)
        draft = Act.with_user(fitter).create({'task_id': task.id, 'kind': 'final', 'signed_by': order.partner_id.name,
                                              'crew_pct': CREW_PCT})
        _photos(env, draft, [('Кухня після монтажу.png', 'prod_kitchen.png'), ('Шафа після монтажу.png', 'prod_wardrobe.png')])
    return {'ready': ready, 'paid_late': paid_late, 'to_sign': to_sign}


def _show_visits(env, show, crew_users, rnd):
    """The show order: two visits on the calendar — bodies first, then the worktop (SALES §6, scene 6)."""
    from .showcase import _work
    task = show.tasks_ids[:1]
    promised = show.commitment_date
    task.write({'name': f'{show.name}: монтаж корпусів', 'date_deadline': _work(promised - timedelta(days=4), rnd),
                'user_ids': [(6, 0, crew_users.ids)]})
    second = task.copy({'name': f'{show.name}: монтаж стільниці', 'date_deadline': _work(promised - timedelta(days=1), rnd),
                        'user_ids': [(6, 0, crew_users.ids)], 'sale_line_id': task.sale_line_id.id})
    env['td.mebli.install.act'].create({'task_id': task.id, 'kind': 'stage', 'crew_pct': 0.0})
    return task | second


def _measures(env, people, show, orders, rnd):
    from .showcase import _backdate, _note
    now = fields.Datetime.now()
    measurer = people['measure']
    Sheet = env['td.mebli.measure'].with_user(measurer)
    # the show order: the fridge is deeper than the column niche (scene 1)
    lead = env['crm.lead'].create({'name': 'Кухня й шафа-купе, квартира', 'type': 'opportunity',
                                   'partner_id': show.partner_id.id, 'user_id': show.user_id.id})
    show.opportunity_id = lead
    sheet = Sheet.create({'lead_id': lead.id, 'order_id': show.id, 'room': 'Кухня й передпокій', 'floor_slope_mm': 6,
                          'wall_angle_deg': 89.5,
                          'utilities': 'Вода й злив — ліва стіна, 450 мм від підлоги; розетки над стільницею — 1100 мм; газу немає.'})
    niches = env['td.mebli.measure.niche'].create([
        {'measure_id': sheet.id, 'sequence': i, 'name': n, 'width_mm': w, 'height_mm': h, 'depth_mm': d}
        for i, (n, w, h, d) in enumerate(SPEC_NICHES)])
    env['td.mebli.measure.appliance'].create([
        {'measure_id': sheet.id, 'sequence': i, 'name': n, 'niche_id': niches[k].id, 'width_mm': w, 'height_mm': h,
         'depth_mm': d} for i, (n, k, w, h, d) in enumerate(SPEC_APPLIANCES)])
    _photos(env, sheet, [('Ніша під холодильник.png', 'prod_kitchen.png'), ('Стіна передпокою.png', 'prod_wardrobe.png'),
                         ('Розетки й вода.png', 'prod_dresser.png')])
    _backdate(env, 'td_mebli_measure', sheet, show.date_order - timedelta(days=3))
    # the background: measurements of the last 30 days, half of them became contracts (KPI 8)
    recent = (orders['done'] | orders['progress'] | orders['confirmed']).filtered(
        lambda o: o.date_order >= now - timedelta(days=28)).sorted('date_order')
    rooms = ['Кухня', 'Передпокій', 'Спальня', 'Дитяча', 'Кабінет']
    for index, order in enumerate(recent[:9]):
        s = Sheet.create({'order_id': order.id, 'room': rnd.choice(rooms), 'floor_slope_mm': rnd.randint(0, 8),
                          'state': 'checked'})
        env['td.mebli.measure.niche'].create({'measure_id': s.id, 'name': 'Стіна під меблі', 'width_mm': rnd.randint(16, 32) * 100,
                                              'height_mm': 2600, 'depth_mm': 650})
        _backdate(env, 'td_mebli_measure', s, order.date_order - timedelta(days=rnd.randint(2, 6)))
    quotes = env['sale.order'].search([('state', 'in', ('draft', 'sent'))])
    for order in quotes[:5]:
        s = Sheet.create({'order_id': order.id, 'room': rnd.choice(rooms), 'floor_slope_mm': rnd.randint(0, 8)})
        _backdate(env, 'td_mebli_measure', s, now - timedelta(days=rnd.randint(3, 20)))
    for name, contact in (('Шафа в нішу, будинок', 'Василь Гордієнко'), ('Кухня, новобудова', 'Алла Захарченко'),
                          ('Гардероб, квартира', 'Богдан Кравчук')):
        lead = env['crm.lead'].create({'name': name, 'type': 'opportunity', 'user_id': people['salon'].id,
                                       'contact_name': contact})
        s = Sheet.create({'lead_id': lead.id, 'room': rnd.choice(rooms)})
        _backdate(env, 'td_mebli_measure', s, now - timedelta(days=rnd.randint(2, 25)))
    _note(sheet, measurer, 'Замір зроблено, фото ніш і комунікацій — у вкладенні. Холодильник клієнта глибший за нішу пенала.',
          show.date_order - timedelta(days=3, hours=-2))
    return sheet


def _claims(env, people, orders, rnd):
    """Claims on installed orders: one closed, two in repair, one overdue (KPI 5, scene 7)."""
    now = fields.Datetime.now()
    acts = env['td.mebli.install.act'].search([('kind', '=', 'final'), ('state', '=', 'signed')], order='signed_on')
    photo = _image('prod_dresser.png')
    rows = [('production', 'company', 'Відшарування кромки на фасаді шухляди', 'done', 6),
            ('installation', 'company', 'Дверка шафи-купе сходить з напрямної', 'under_repair', 0),
            ('supplier', 'supplier', 'Тріщина фарби на фасаді МДФ', 'confirmed', 0),
            ('transport', 'company', 'Подряпина бокової панелі після доставки', 'confirmed', 0)]
    # the reasons are the standard repair tags (configuration of the customer, A-12), who pays — «Under Warranty»
    names = {'production': 'Виробництво', 'installation': 'Монтаж', 'supplier': 'Постачальник', 'transport': 'Транспорт',
             'customer': 'Клієнт'}
    tags = {key: env['repair.tags'].search([('name', '=', name)], limit=1)
            or env['repair.tags'].create({'name': name, 'color': color})
            for color, (key, name) in enumerate(names.items(), start=1)}
    claims, dates = env['repair.order'], []
    for act, (reason, payer, text, state, days) in zip(acts[-8::2], rows):
        order = act.order_id
        line = order.order_line.filtered('td_bom_id')[:1]
        part = line.td_bom_id.td_part_ids.filtered(lambda p: p.rule_id.material_role == 'facade_board')[:1]
        claim = env['repair.order'].create({
            'partner_id': order.partner_id.id, 'product_id': line.product_id.id, 'td_claim_order_id': order.id,
            'td_part_id': part.id, 'tag_ids': [(6, 0, tags[reason].ids)], 'under_warranty': payer != 'customer',
            'td_photo': photo,
            'internal_notes': f'<p>{text}</p>', 'user_id': people['chief'].id,
            'schedule_date': act.signed_on + timedelta(days=10 if state != 'confirmed' or reason != 'transport' else 3)})
        created = act.signed_on + timedelta(days=rnd.randint(2, 4))
        if state in ('confirmed', 'under_repair', 'done'):
            claim.action_validate()
            if claim.state == 'draft':  # the stock check may ask a question: the product is at the customer, confirm
                claim._action_repair_confirm()
        if state in ('under_repair', 'done'):
            claim.action_repair_start()
        if state == 'done':
            claim.action_repair_end()
        claims |= claim
        dates.append((created, created + timedelta(days=days) if days else now, claim.id))
    # the transport claim is overdue: its date has passed
    overdue = claims.filtered(lambda c: tags['transport'] in c.tag_ids)
    overdue.schedule_date = now - timedelta(days=2)
    env.flush_all()
    for row in dates:  # after all writes: the dates of the claims (a closed one took 6 days)
        env.cr.execute('UPDATE repair_order SET create_date = %s, write_date = %s WHERE id = %s', row)
    claims.invalidate_recordset()
    return claims


def _price_history(env, rnd):
    """Purchases of the standard materials over half a year; this month the fittings got dearer (S-08, NP-02)."""
    from .dates import _receive
    now = fields.Datetime.now()
    suppliers = [env['res.partner'].create({'name': name, 'is_company': True, 'city': city, 'country_id': env.ref('base.ua').id,
                                            'phone': f'+380 00 000 02 {index:02d}', 'email': f'sales{index}@supplier.example'})
                 for index, (name, city) in enumerate(MATERIAL_SUPPLIERS, start=1)]
    lines = env['purchase.order.line']
    for xmlid, (supplier, price, qty) in PRICE_HISTORY.items():
        product = env.ref(f'td_mebli_demo.{xmlid}')
        for days in (150, 115, 80, 52, 34, 9):
            jump = PRICE_JUMP.get(xmlid, 1.0) if days < 30 else 1.0
            unit = round(price * rnd.uniform(0.98, 1.03) * jump, 2)
            when = now - timedelta(days=days, hours=rnd.randint(1, 6))
            order = env['purchase.order'].create({'partner_id': suppliers[supplier].id, 'user_id': False,
                                                  'order_line': [(0, 0, {'product_id': product.id, 'product_qty': qty,
                                                                         'price_unit': unit, 'date_planned': when})]})
            order.button_confirm()
            order.write({'date_order': when, 'date_approve': when})
            for picking in order.picking_ids:
                _receive(picking)
            lines |= order.order_line
    lines = env['purchase.order.line'].search([('product_id', '!=', False)])
    for name in ('td_history_price', 'td_price_delta_pct', 'td_overpay', 'td_over_history'):
        env.add_to_compute(lines._fields[name], lines)
    lines.flush_recordset()


def _change(env, show):
    """Version 2 of the show order: the customer chose painted fronts — the price and the promised date moved (scene 3)."""
    promised = fields.Date.to_date(show.commitment_date)
    env['td.mebli.order.change'].create({
        'order_id': show.id, 'version': 2, 'reason': 'customer', 'note': 'Фасади кухні — фарбований МДФ RAL 9010 замість плівкового',
        'state': 'done', 'amount_before': round(show.amount_untaxed - 8400.0, 2), 'amount_after': show.amount_untaxed,
        'date_before': promised - timedelta(days=7), 'date_after': promised})


def _accruals(env, people, crew):
    Accrual = env['td.mebli.accrual']
    Accrual.action_td_accrue()
    today = fields.Date.context_today(Accrual)
    by_name = {e.name: e for e in env['hr.employee'].search([])}
    Accrual.create([
        {'employee_id': by_name['Василь Ткач'].id, 'kind': 'bonus', 'amount': 1500.0, 'date': today - timedelta(days=3),
         'reason': 'Термінове кромкування фасадів без браку'},
        {'employee_id': by_name['Сергій Бондаренко'].id, 'kind': 'penalty', 'amount': -800.0, 'date': today - timedelta(days=6),
         'reason': 'Повторне складання: перекіс шухляди'},
        {'employee_id': crew[-1:].id, 'kind': 'bonus', 'amount': 1000.0, 'date': today - timedelta(days=2),
         'reason': 'Фото з акта погоджено для реклами'}])


def _open_dates(env, orders, rnd, skip):
    """Two orders still in the workshop are late through the workshop (reason «Company»), the rest keep their date."""
    open_orders = orders['progress'].filtered(
        lambda o: o not in skip and o.delivery_status != 'full'
        and o.mrp_production_ids.filtered(lambda p: p.state == 'progress'))
    for order in open_orders.sorted('date_order')[-2:]:
        order.commitment_date = fields.Datetime.to_datetime(order._td_shop_date() - timedelta(days=rnd.randint(2, 5))) \
            + timedelta(hours=15)


def _calibrate_load(env, targets):
    """Weekly hours of the sections (standard calendars) so that the open work of the next 7 days gives one bottleneck."""
    from .showcase import _section_calendar
    start, end = env['td.mebli.dashboard']._week()
    work = env['mrp.workorder'].search([('state', 'not in', ('done', 'cancel')), ('date_start', '!=', False),
                                        ('date_start', '<', end)])
    for code, percent in targets.items():
        center = env['mrp.workcenter'].search([('code', '=', code)], limit=1)
        hours = sum(work.filtered(lambda w: w.workcenter_id == center).mapped('td_expected_hours'))
        if not (center and hours):
            continue
        weekly = max(1.0, hours / percent * 100.0)
        parallel = max(1, math.ceil(weekly / 40.0))
        general = center.capacity_ids.filtered(lambda c: not c.product_id)
        if general:
            general[:1].capacity = parallel
            general[1:].unlink()
        else:
            center.capacity_ids = [(0, 0, {'product_uom_id': env.ref('uom.product_uom_unit').id, 'capacity': parallel})]
        center.resource_calendar_id = _section_calendar(env, center, round(weekly / parallel, 1))


def seed_full(env, people, partners, orders, show, rnd):
    by_center, team, crew = _employees(env, people)
    crew_users = people['fitter'] | people['fitter2']
    state = _installations(env, people, orders, crew, rnd)
    _shop_history(env, by_center, team, rnd)
    _show_visits(env, show, crew_users, rnd)
    _measures(env, people, show, orders, rnd)
    _claims(env, people, orders, rnd)
    _price_history(env, rnd)
    _change(env, show)
    _accruals(env, people, crew)
    _open_dates(env, orders, rnd, show | state['ready'] | state['paid_late'] | state['to_sign'])
    # exchange status with BAS (imitation): finished orders are sent, one with an error to show the state
    done = orders['done']
    done.write({'td_bas_state': 'sent'})
    done[-1:].write({'td_bas_state': 'error'})
    env['res.currency'].with_context(active_test=False).search([('name', 'in', ('EUR', 'USD'))]).write({'active': True})
    env['res.currency'].td_update_nbu_rates({'EUR': 48.3, 'USD': 41.6}, imitation=True)  # imitation rates, not real ones
    _calibrate_load(env, {'CUT': 74, 'EDG': 112, 'DRL': 83, 'ASM': 91})
    return state
