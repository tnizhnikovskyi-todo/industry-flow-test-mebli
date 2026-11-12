// Кроки десктопного сценарію зрізу A-21 (спроба 2), ПОВНИЙ ОБСЯГ — хвиля 1 підготувала, знімає хвиля 2 (PLAN.md §1 «Повний обсяг», §6).
// Порядок — SALES §6 за записом 36: крок 0 (прийнятий зразок, S-02, сцена 4) першим; дашборд S-19 — останнім.
// Замовлення показу S00123 — env ORDER_ID (типово 123: id замовлення з «Посиланням клієнта» «Кухня й шафа-купе, квартира»).
// Селектори не перевірені на живому записі: хвиля 2 звіряє їх на demo-mebli-full і правит лише цей файл.
const ORDER = process.env.ORDER_ID || '123';
const CSV = new URL('./data/kitchen-spec.csv', import.meta.url).pathname;
const row = (c, text) => c.page.locator('.o_data_row', { hasText: text });
const tab = (c, text) => c.page.locator('.o_notebook_headers a', { hasText: text });
const btn = (c, text) => c.page.locator('button', { hasText: text });
// доробка коробки A (COVERAGE-REVIEW §2.1, A1–A4): id записів демо-бази (детерміновані seed; перевизначаються env після перезбирання)
const ID = {
    noPayOrder: process.env.NOPAY_ORDER_ID || '0', noPayTask: process.env.NOPAY_TASK_ID || '0',
    paidOrder: process.env.PAID_ORDER_ID || '0', cutOrder: process.env.CUT_ORDER_ID || '0', cutJob: process.env.CUT_JOB_ID || '0',
    act: process.env.PDF_ACT_ID || '0', kitOrder: process.env.KIT_ORDER_ID || '0',
};
// хвиля 2 позицій збірки (F-49…F-65): id записів демо-бази з параметра td_mebli_demo.shot_ids (seed wave2.py) — env SHOT_IDS (JSON; shoot/ids.sh)
const W2 = JSON.parse(process.env.SHOT_IDS || '{}');
const XLSX = new URL('./data/kitchen-spec.xlsx', import.meta.url).pathname;
const PRICES = new URL('./data/supplier-prices.xlsx', import.meta.url).pathname;
const PDF_DIR = new URL('../pdf/', import.meta.url).pathname;
const SCREENS = new URL('../screens/', import.meta.url).pathname;
// друкована форма: справжній PDF (wkhtmltopdf Odoo, маршрут /report/pdf) -> pdf/<ім'я>.pdf і перша сторінка -> screens/<ім'я>-pdf-p1.png;
// сам крок знімає HTML-рендер того самого шаблону (/report/html) — для DOM-перевірки мови й кадру
async function savePdf(c, report, id, name) {
    const fs = await import('fs'); const { execFileSync } = await import('child_process');
    const base = process.env.BASE || 'http://127.0.0.1:8069';
    const res = await c.page.request.get(`${base}/report/pdf/${report}/${id}`);
    const body = await res.body();
    if (!res.ok() || body.subarray(0, 4).toString() !== '%PDF') throw new Error(`PDF ${report}/${id}: ${res.status()} ${body.subarray(0, 40)}`);
    fs.mkdirSync(PDF_DIR, { recursive: true });
    fs.writeFileSync(`${PDF_DIR}${name}.pdf`, body);
    execFileSync('pdftoppm', ['-png', '-r', '110', '-f', '1', '-l', '1', '-singlefile', `${PDF_DIR}${name}.pdf`, `${SCREENS}${name}-pdf-p1`]);
}

const ALL = [
    // сцена 4 — замовні фасади затримуються (зразок, прийнято)
    // ім'я кроку — не 'sample': прийнятий кадр зразка screens/00-sample.png не перезаписується (рішення AI 0.3.x, PLAN §7)
    { n: 0, role: 'salon', url: `/odoo/action-sale.action_orders/${ORDER}`, name: 'late-facades',
      act: async (c, { press }) => { await press(c, tab(c, 'Закупівлі під замовлення')); },
      facts: [
          { name: 'promised_date', sel: '.o_field_widget[name=commitment_date]' },
          { name: 'forecast_date', sel: '.o_field_widget[name=td_forecast_date]' },
          { name: 'delay_days', sel: '.o_group .o_field_widget[name=td_delay_days]', re: '\\d+' },
          { name: 'late_item', sel: '.td_date_alert .o_field_widget[name=td_late_item]' },
          { name: 'late_item_supplier_date', sel: '.o_data_row.text-danger td[name=date_planned]' },
          { name: 'late_item_ready', sel: '.o_data_row.text-danger td[name=td_date_ready]' },
          { name: 'late_purchase', sel: '.o_data_row.text-danger td[name=order_id]' },
      ] },
    // сцена 1 — замір із помилкою (S-15): холодильник глибший за нішу пенала
    { n: 1, role: 'measure', url: '/odoo/action-td_mebli_measure.td_mebli_measure_action', name: 'measure',
      act: async (c, { press }) => {
          await press(c, row(c, 'Кухня й передпокій').locator('td[name=name]'));
          await press(c, tab(c, 'Техніка клієнта'));
      },
      facts: [
          { name: 'issue', sel: '.alert-danger .o_field_widget[name=issue_text]' },
          { name: 'fridge_check', sel: '.o_data_row.text-danger td[name=issue]' },
      ] },
    // сцена 1а — ціна з розмірів у рядку замовлення (конфігуратор td_mebli_sale)
    { n: 2, role: 'salon', url: `/odoo/action-sale.action_orders/${ORDER}`, name: 'price-from-size',
      facts: [
          { name: 'line_price', sel: '.o_data_row:first-child td[name=price_unit]' },
          { name: 'margin_percent', sel: '.o_field_widget[name=margin_percent]', re: '[\\d,.]+\\s*%' },
      ] },
    // сцена 2 — імпорт специфікації з CSV (S-03): розпізнавання колонок (змінює дані — PASS1)
    { n: 3, role: 'tech', url: '/odoo/action-mrp.mrp_bom_form_action', name: 'csv-import',
      act: async (c, { press, typeIn }) => {
          await typeIn(c, c.page.locator('.o_searchview_input'), 'S00123/391'); await c.page.keyboard.press('Enter'); await c.page.waitForTimeout(1200);
          await press(c, row(c, 'S00123/391').locator('td').nth(1));
          await press(c, c.page.locator('.o_cp_action_menus button, .o_cp_action_menus .dropdown-toggle').first());
          await press(c, c.page.locator('.dropdown-item', { hasText: 'Імпорт деталей' }));
          await c.page.locator('.modal input[type=file]').setInputFiles(CSV);
          await press(c, btn(c, 'Розпізнати колонки'));
      },
      facts: [{ name: 'parts_in_file', sel: '.modal .o_field_widget[name=preview_count]' }] },
    // сцена 3 — зміна фасадів (B): версія 2, причина «Клієнт», ціна й дата
    { n: 4, role: 'salon', url: `/odoo/action-sale.action_orders/${ORDER}`, name: 'change',
      act: async (c, { press }) => { await press(c, tab(c, 'Зміни')); },
      facts: [
          { name: 'change_shift_days', sel: '.o_data_row td[name=shift_days]' },
          { name: 'change_amount_delta', sel: '.o_data_row td[name=amount_delta]' },
      ] },
    // сцена 5 — планшет цеху: «Взято» з PIN (PASS1)
    { n: 5, role: 'tablet', url: '/odoo/action-td_mebli_shop.mrp_workorder_td_tablet_action', name: 'tablet',
      act: async (c, { press, typeIn }) => {
          await press(c, c.page.locator('.o_group_header', { hasText: 'Розкрій' }));
          await press(c, c.page.locator('.o_data_row', { hasText: 'WH/MO/00109' }).locator('button', { hasText: 'Взято' }));
          // кіоск: працівник — зі списку (на телефоні пошуковий діалог співробітників недоступний ролі планшета)
          await press(c, c.page.locator('.modal .o_field_widget[name=employee_id] input'));
          await press(c, c.page.locator('.o_select_menu_item', { hasText: 'Олег Дорошенко' })); await c.page.waitForTimeout(400);
          await typeIn(c, c.page.locator('.modal .o_field_widget[name=pin] input'), '1212');
          await press(c, btn(c, 'Підтвердити'));
      },
      facts: [{ name: 'in_work', sel: '.o_data_row:has-text("WH/MO/00109") td[name=td_worker_names]' }] },
    // сцена 5 — комплектувальний лист: неповний комплект не відвантажується (PASS1: спроба «Перевірити»)
    { n: 6, role: 'store', url: '/odoo/action-td_mebli_shop.td_mebli_kit_line_action', name: 'kit',
      act: async (c, { press }) => {
          await press(c, c.page.locator('.o_searchview_facet .o_facet_remove').first());
          await press(c, c.page.locator('.o_filter_menu, .o_searchview_dropdown_toggler').first());
          await press(c, c.page.locator('.o-dropdown-item, .dropdown-item', { hasText: 'Не запаковано' }));
          await c.page.keyboard.press('Escape');
      },
      facts: [{ name: 'missing_rows', sel: '.o_list_renderer', re: 'Задня стінка[^\\n]*' }] },
    // сцена 5а — ділові обрізки в обліку за декором (OUT-02: форма завдання з картою розкрою-імітацією в кадр не йде;
    // пакет розкрою за декором — у кліпі D_cutting: нове завдання з кількох МО, без результату оптимізатора)
    { n: 7, role: 'tech', url: '/odoo/action-td_mebli_cutting.stock_lot_td_offcut_action', name: 'offcuts',
      facts: [{ name: 'offcut_lots', sel: '.o_pager_limit, .o_group_header', re: '\\d+' }] },
    { n: 8, role: 'tech', url: '/odoo/action-td_mebli_shop.td_mebli_quality_check_action', name: 'quality',
      facts: [{ name: 'failed_check', sel: '.o_list_renderer tbody .o_data_row.text-danger', re: 'WH/MO/\\d+' }] },
    // сцена 6 — календар монтажів, два виїзди S00123; акти
    { n: 9, role: 'fitter', url: '/odoo/action-td_mebli_install.td_mebli_install_calendar_action', name: 'install-calendar',
      facts: [{ name: 'show_visits', sel: '.o_calendar_renderer', re: 'S00123: монтаж корпусів.*S00123: монтаж стільниці' }] },
    { n: 10, role: 'fitter', url: '/odoo/action-td_mebli_install.td_mebli_install_act_action', name: 'acts',
      facts: [{ name: 'crew_total', sel: 'tfoot td[name=crew_amount], tfoot .o_list_number', re: '[\\d\\s ,.]+' }] },
    // сцена 6/8 — нарахування: відрядна, % бригаді, премія і штраф з причиною
    { n: 11, role: 'fin', url: '/odoo/action-td_mebli_install.td_mebli_accrual_action', name: 'accruals',
      facts: [{ name: 'accrual_total', sel: '.o_pivot tbody tr:first-child td:last-child' }] },
    // сцена 7 — рекламації (канбан Ремонту) і собівартість план ↔ факт
    { n: 12, role: 'chief', url: '/odoo/action-td_mebli_claim.td_mebli_claim_action', name: 'claims',
      facts: [{ name: 'overdue', sel: '.o_kanban_record .text-bg-danger' }] },
    { n: 13, role: 'fin', url: '/odoo/action-td_mebli_cost.sale_order_td_cost_fact_action', name: 'plan-fact',
      facts: [{ name: 'fact_total', sel: 'tfoot td' }] },
    // S-08 — ціни постачальників понад історію
    { n: 14, role: 'owner', url: '/odoo/action-td_mebli_purchase.purchase_order_line_td_price_action', name: 'prices',
      act: async (c, { press }) => {
          await press(c, c.page.locator('.o_searchview_dropdown_toggler').first());
          await press(c, c.page.locator('.o-dropdown-item, .dropdown-item', { hasText: 'Понад історію' }));
          await c.page.keyboard.press('Escape');
      },
      facts: [{ name: 'overpay_total', sel: 'tfoot td[name=td_overpay], tfoot .o_list_number' }] },
    // сцена 8 — дашборд керівника (останнім); картка = drill-down
    { n: 15, role: 'owner', url: '/odoo/action-td_mebli_dashboard.action_dashboard', name: 'dashboard',
      facts: [
          { name: 'margin', sel: '.td_card.td_k_margin .td_value' },
          { name: 'shift', sel: '.td_card.td_k_shift .td_value' },
          { name: 'on_time', sel: '.td_card.td_k_on_time .td_value' },
          { name: 'prices', sel: '.td_card.td_k_prices .td_value' },
          { name: 'claims', sel: '.td_card.td_k_claims .td_value' },
          // DASH-drill: кількість замовлень картки маржі = кількість записів звіту drill-down (крок 16)
          { name: 'margin_orders', sel: '.td_card.td_k_margin', re: '(?<=замовлень )\\d+' },
      ] },
    { n: 16, role: 'owner', url: '/odoo/action-td_mebli_dashboard.action_dashboard', name: 'dashboard-drill-margin',
      act: async (c, { press }) => { await press(c, c.page.locator('.td_card.td_k_margin')); },
      facts: [
          { name: 'margin_orders', sel: '.o_pager_limit' },
          // DASH-drill: підсумки «Виручка» і «Маржа план» = рядок картки «Маржа … з виручки …» (картка = маржа ÷ виручка)
          { name: 'revenue_total', sel: 'tfoot td:nth-child(2)' },
          { name: 'margin_total', sel: 'tfoot td:nth-child(3)' },
          { name: 'plan_cost_total', sel: 'tfoot td:nth-child(4)' },
      ] },
    // сцена 2 — пропозиція до підтвердження: маржа видно ДО запуску (не 100 %: планова собівартість у чернетці)
    { n: 17, role: 'salon', url: '/odoo/action-sale.action_quotations/117', name: 'quotation-margin',
      facts: [
          { name: 'state', sel: '.o_statusbar_status .o_arrow_button_current' },
          { name: 'margin_percent', sel: '.o_field_widget[name=margin_percent]', re: '[\\d,.]+\\s*%' },
      ] },
    // запит власника «чому деталі окремою сторінкою»: деталі там, де працюють (лише читання, PLAN §7)
    // сцена 2 — виробниче замовлення шафи-купе S00123, вкладка «Деталі» (деталі специфікації замовлення, підсумки на все МО);
    // перехід з імпорту CSV у МО кухонного модуля — у кліпі D_csv (імпорт не перераховує плиту — PLAN §7, беклог A-11)
    { n: 18, role: 'tech', url: '/odoo/action-mrp.mrp_production_action', name: 'mo-parts',
      act: async (c, { press, typeIn }) => {
          await typeIn(c, c.page.locator('.o_searchview_input'), 'WH/MO/00110'); await c.page.keyboard.press('Enter'); await c.page.waitForTimeout(1200);
          await press(c, row(c, 'WH/MO/00110').locator('td[name=name]'));
          await press(c, tab(c, 'Деталі'));
      },
      facts: [{ name: 'part_count', sel: '.o_field_widget[name=td_part_count]' },
              { name: 'board_area_m2', sel: '.o_field_widget[name=td_board_area_m2]' }] },
    // сцена 2/5 — компоненти МО шафи-купе: плита й кромка позначені «З деталей» (кількість розраховано з деталей)
    { n: 19, role: 'tech', url: '/odoo/action-mrp.mrp_production_action', name: 'mo-from-parts',
      act: async (c, { press, typeIn }) => {
          await typeIn(c, c.page.locator('.o_searchview_input'), 'WH/MO/00110'); await c.page.keyboard.press('Enter'); await c.page.waitForTimeout(1200);
          await press(c, row(c, 'WH/MO/00110').locator('td[name=name]'));
          await press(c, tab(c, 'Компоненти'));
      },
      facts: [{ name: 'from_parts_first', sel: '.o_field_widget[name=move_raw_ids] .o_data_row:has(td[name=td_from_parts] input:checked) td[name=product_id]' }] },
    // сцена 5 — планшет цеху: «Деталі» завдання розкрою (діалог лише читання: деталь, матеріал, к-сть, Д×Ш, кромка)
    { n: 20, role: 'tablet', url: '/odoo/action-td_mebli_shop.mrp_workorder_td_tablet_action', name: 'tablet-parts',
      act: async (c, { press }) => {
          await press(c, c.page.locator('.o_group_header', { hasText: 'Розкрій' }));
          // WH/MO/00110 у проході 1 завершено (M_tablet) і зі списку «До виконання» зникає: кухонний модуль WH/MO/00109 (у роботі з кроку 5)
          await press(c, c.page.locator('.o_data_row', { hasText: 'WH/MO/00109' }).locator('button', { hasText: 'Деталі' }).first());
      },
      facts: [{ name: 'part_count', sel: '.modal .o_field_widget[name=td_part_count]' }] },
    // ---- доробка коробки A (COVERAGE-REVIEW §2.1): A1 графік оплат і контроль доплати, A3 порізка в дистриб'ютора, A4 етапи дошки, A2 друковані форми
    // A1 — графік оплат = стандартні умови оплати (3 рядки), нове лише «Етап оплати» рядка
    { n: 21, role: 'fin', url: '/odoo/action-account.action_payment_term_form', name: 'pay-schedule',
      act: async (c, { press }) => { await press(c, row(c, 'перед монтажем').locator('td').nth(1)); },
      facts: [{ name: 'milestones', sel: '.o_field_widget[name=line_ids]', re: 'Передоплата[\\s\\S]*Перед монтажем[\\s\\S]*Після акта' }] },
    // A1 — замовлення змонтоване наполовину: доплати перед монтажем немає — попередження в замовленні
    { n: 22, role: 'fin', url: `/odoo/action-sale.action_orders/${ID.noPayOrder}`, name: 'order-no-payment',
      facts: [{ name: 'missing', sel: '.td_pay_alert .o_field_widget[name=td_pay_missing]' },
              { name: 'received', sel: '.td_pay_alert .o_field_widget[name=td_pay_received]' },
              { name: 'due', sel: '.td_pay_alert .o_field_widget[name=td_pay_before_install]' }] },
    // A1 — той самий виїзд у бригадира: попередження на задачі виїзду (режим «Попереджати» за замовчуванням)
    { n: 23, role: 'fitter', url: `/odoo/action-td_mebli_install.td_mebli_install_calendar_action/${ID.noPayTask}`, name: 'visit-no-payment',
      facts: [{ name: 'missing', sel: '.td_pay_alert .o_field_widget[name=td_pay_missing]' }] },
    // A3 — порізка в дистриб'ютора: стандартна закупівля послуги, дата повернення деталей
    { n: 24, role: 'tech', url: `/odoo/action-td_mebli_cutting.td_mebli_cutting_job_action/${ID.cutJob}`, name: 'cutting-distributor',
      facts: [{ name: 'distributor', sel: '.o_field_widget[name=distributor_id]' },
              { name: 'return_date', sel: '.o_field_widget[name=return_date]' },
              { name: 'purchase', sel: '.o_field_widget[name=purchase_id]' }] },
    // A3 — прогнозна дата з порізкою: банер причини зсуву «Порізка в дистриб'ютора»
    { n: 25, role: 'chief', url: `/odoo/action-sale.action_orders/${ID.cutOrder}`, name: 'date-cutting',
      facts: [{ name: 'promised_date', sel: '.o_field_widget[name=commitment_date]' },
              { name: 'forecast_date', sel: '.o_field_widget[name=td_forecast_date]' },
              { name: 'delay_days', sel: '.o_group .o_field_widget[name=td_delay_days]', re: '\\d+' },
              { name: 'reason', sel: '.o_group .o_field_widget[name=td_delay_reason]' }] },
    // A4 — дошка замовлень: етапи після «Виготовлено» (прокрутка вправо до «Закрито»)
    { n: 26, role: 'chief', url: '/odoo/action-td_mebli_sale.action_orders_board_td_mebli', name: 'board-stages',
      act: async (c) => {
          await c.page.locator('.o_kanban_group').last().scrollIntoViewIfNeeded();
          await c.page.evaluate(() => document.querySelectorAll('.o_kanban_renderer, .o_content').forEach((el) => { el.scrollLeft = el.scrollWidth; }));
          await c.page.waitForTimeout(600);
      },
      facts: [{ name: 'stages', sel: '.o_kanban_renderer', re: 'Виготовлено[\\s\\S]*Очікує клієнта[\\s\\S]*Відвантажено / на доставці[\\s\\S]*Монтаж[\\s\\S]*Закрито' },
              { name: 'waiting', sel: '.o_kanban_group:has(.o_column_title:has-text("Очікує клієнта")) .o_kanban_record', re: 'S\\d+' },
              { name: 'shipped', sel: '.o_kanban_group:has(.o_column_title:has-text("Відвантажено")) .o_kanban_record', re: 'S\\d+' }] },
    // A2 — друковані форми (PDF): договір (підряд, графік оплат, позначка юриста), акт монтажу, комплектувальний лист
    { n: 27, role: 'owner', url: `/report/html/td_mebli_sale.report_contract/${ID.paidOrder}`, name: 'contract-pdf',
      act: async (c) => { await savePdf(c, 'td_mebli_sale.report_contract', ID.paidOrder, '27-contract'); },
      facts: [{ name: 'lawyer_mark', sel: '.td_lawyer_mark' },
              { name: 'schedule', sel: '.td_pay_schedule tbody', re: 'Передоплата[\\s\\S]*Перед монтажем[\\s\\S]*Після акта' }] },
    { n: 28, role: 'owner', url: `/report/html/td_mebli_install.report_install_act/${ID.act}`, name: 'act-pdf',
      act: async (c) => { await savePdf(c, 'td_mebli_install.report_install_act', ID.act, '28-act'); },
      facts: [{ name: 'title', sel: '.td_report_act h2' }] },
    { n: 29, role: 'owner', url: `/report/html/td_mebli_shop.report_kit/${ID.kitOrder}`, name: 'kit-pdf',
      act: async (c) => { await savePdf(c, 'td_mebli_shop.report_kit', ID.kitOrder, '29-kit'); },
      facts: [{ name: 'places', sel: '.td_report_kit .row .col-4:first-child', re: '\\d+' }] },
    // ---- хвиля 2 позицій збірки (flow/decisions.md 42–47; F-49…F-65): стандарт перш за все
    // F-50 — сповіщення менеджеру: стандартна дія «Зсув прогнозної дати» на замовленні (чаттер, «Заплановані дії»)
    { n: 30, role: 'salon', url: `/odoo/action-sale.action_orders/${ORDER}`, name: 'forecast-activity',
      act: async (c) => { await c.page.locator('.o-mail-Activity').first().scrollIntoViewIfNeeded().catch(() => {}); },
      facts: [{ name: 'activity', sel: '.o-mail-Activity', re: 'Прогноз[^\\n]*' }] },
    // F-51 — лист «нова дата»: стандартний редактор листа з шаблоном (не надсилаємо)
    { n: 31, role: 'salon', url: `/odoo/action-sale.action_orders/${ORDER}`, name: 'new-date-letter',
      act: async (c, { press }) => { await press(c, c.page.locator('button[name=action_td_notify_new_date]')); await c.page.waitForTimeout(1200); },
      facts: [{ name: 'new_date', sel: '.modal .o_field_widget[name=body]', re: '(?<=Нова дата: )[\\d.]+\\d' }] },
    // F-51 — нагадування про доплату перед монтажем у чаттері замовлення (у черзі пошти)
    { n: 32, role: 'fin', url: `/odoo/action-sale.action_orders/${W2.payment_letter_order || 0}`, name: 'payment-reminder',
      act: async (c) => { await c.page.locator('.o-mail-Message', { hasText: 'доплатити' }).first().scrollIntoViewIfNeeded().catch(() => {}); },
      facts: [{ name: 'letter_due', sel: '.o-mail-Message:has-text("доплатити") .o-mail-Message-body', re: '(?<=доплатити: )[\\d\\s ,]+₴' }] },
    // F-62 — перевірка проєкту за заміром перед розкроєм: діалог на «Надіслати на розкрій» (завдання з кліпу D_cutting; не надсилаємо)
    { n: 33, role: 'tech', url: '/odoo/action-td_mebli_cutting.td_mebli_cutting_job_action', name: 'measure-check',
      act: async (c, { press }) => {
          await press(c, c.page.locator('.o_data_row', { hasText: 'Чернетка' }).first().locator('td').nth(1));
          await press(c, c.page.locator('button[name=action_send]'));
          await c.page.waitForTimeout(800);
      },
      facts: [{ name: 'problems', sel: '.modal .o_field_widget[name=problems]' }] },
    // F-63 — надійність постачальника: середнє запізнення поруч зі стандартним «вчасно, %»
    { n: 34, role: 'store', url: `/odoo/action-account.res_partner_action_supplier/${W2.stone_supplier || 0}`, name: 'supplier-reliability',
      facts: [{ name: 'avg_delay', sel: '.o_field_widget[name=td_supplier_delay_avg]' },
              { name: 'on_time', sel: '.o_field_widget[name=on_time_rate]' }] },
    // F-52 — перевитрата матеріалу: стандартне попередження при закритті МО (PASS1: «Виготовлено» відкриває діалог)
    { n: 35, role: 'chief', url: `/odoo/action-mrp.mrp_production_action/${W2.consumption_mo || 0}`, name: 'consumption',
      act: async (c, { press }) => { await press(c, c.page.locator('.o_form_statusbar button[name=button_mark_done]').first()); await c.page.waitForTimeout(1200); },
      facts: [{ name: 'dialog', sel: '.modal .modal-title' }] },
    // F-01 (позиція 4) — імпорт специфікації з Excel (.xlsx): колонки розпізнано (не імпортуємо)
    { n: 36, role: 'tech', url: '/odoo/action-mrp.mrp_bom_form_action', name: 'xlsx-import',
      act: async (c, { press, typeIn }) => {
          await typeIn(c, c.page.locator('.o_searchview_input'), 'S00123/391'); await c.page.keyboard.press('Enter'); await c.page.waitForTimeout(1200);
          await press(c, row(c, 'S00123/391').locator('td').nth(1));
          await press(c, c.page.locator('.o_cp_action_menus button, .o_cp_action_menus .dropdown-toggle').first());
          await press(c, c.page.locator('.dropdown-item', { hasText: 'Імпорт деталей' }));
          await c.page.locator('.modal input[type=file]').setInputFiles(XLSX);
          await c.page.waitForTimeout(600);
          await press(c, btn(c, 'Розпізнати колонки'));
      },
      facts: [{ name: 'parts_in_file', sel: '.modal .o_field_widget[name=preview_count]' }] },
    // F-59 — прайс постачальника з Excel у стандартні ціни постачальника (перегляд; не записуємо)
    { n: 37, role: 'store', url: '/odoo/action-td_mebli_purchase.td_mebli_price_import_action', name: 'price-import',
      act: async (c, { press, typeIn }) => {
          await typeIn(c, c.page.locator('.modal .o_field_widget[name=partner_id] input'), 'Плита-Трейд');
          await press(c, c.page.locator('.o-autocomplete--dropdown-item', { hasText: 'Плита-Трейд' }).first());
          await c.page.locator('.modal input[type=file]').setInputFiles(PRICES);
          await c.page.waitForTimeout(600);
          await press(c, btn(c, 'Розпізнати колонки'));
          await c.page.mouse.move(5, 5); await c.page.waitForTimeout(300);
      },
      facts: [{ name: 'to_write', sel: '.modal .o_field_widget[name=change_count]' },
              { name: 'not_found', sel: '.modal .o_field_widget[name=unknown_count]' }] },
    // F-29 — етикетки деталей з QR (PDF з комплектувального листа)
    { n: 38, role: 'owner', url: `/report/html/td_mebli_shop.report_part_labels/${ID.kitOrder}`, name: 'labels-pdf',
      act: async (c) => { await savePdf(c, 'td_mebli_shop.report_part_labels', ID.kitOrder, '38-labels'); },
      facts: [{ name: 'last_label', sel: '.td_label_code' }] },
    // F-53 — візуалізація дизайнера в стандартному PDF пропозиції
    { n: 39, role: 'salon', url: `/report/html/sale.report_saleorder/${ORDER}`, name: 'quote-visual-pdf',
      act: async (c) => { await savePdf(c, 'sale.report_saleorder', ORDER, '39-quote-visual'); },
      facts: [{ name: 'visual', sel: '.td_design_visual h5' }] },
    // F-56 — акт приймання-передачі без монтажу (з відвантаження)
    { n: 40, role: 'store', url: `/report/html/td_mebli_shop.report_handover_act/${W2.handover_picking || 0}`, name: 'handover-act-pdf',
      act: async (c) => { await savePdf(c, 'td_mebli_shop.report_handover_act', W2.handover_picking || 0, '40-handover-act'); },
      facts: [{ name: 'title', sel: '.td_report_handover h2' }] },
    // F-58 — денний план бригади (PDF бригадира: виїзди найближчих днів, сторінка на день)
    { n: 41, role: 'fitter', url: `/report/html/td_mebli_install.report_day_plan_user/${W2.fitter_user || 0}`, name: 'day-plan-pdf',
      act: async (c) => { await savePdf(c, 'td_mebli_install.report_day_plan_user', W2.fitter_user || 0, '41-day-plan'); },
      facts: [{ name: 'visits', sel: '.td_report_day_plan tbody', re: 'S\\d+' }] },
    // F-54 — календар замірника: вільні вікна й запис з нагоди CRM (не записуємо)
    { n: 42, role: 'salon', url: `/odoo/action-crm.crm_lead_action_pipeline/${W2.booking_lead || 0}`, name: 'measure-booking',
      act: async (c, { press }) => { await press(c, c.page.locator('button[name=action_td_book_measure]')); await c.page.waitForTimeout(1000); },
      facts: [{ name: 'windows', sel: '.modal .td_measure_slots .o_data_row:first-child' }] },
    // F-55 — платний ремонт після гарантії: стандартний Ремонт, пропозиція й рахунок клієнту
    { n: 43, role: 'chief', url: `/odoo/action-td_mebli_claim.td_mebli_claim_action/${W2.paid_repair || 0}`, name: 'paid-repair',
      facts: [{ name: 'warranty_end', sel: '.td_warranty_alert .o_field_widget[name=td_warranty_end]' }] },
    // F-60 — обслуговування верстатів: поломка, простій дільниці в стандартному журналі часу
    { n: 44, role: 'chief', url: `/odoo/action-maintenance.hr_equipment_request_action/${W2.breakdown || 0}`, name: 'maintenance',
      facts: [{ name: 'workcenter', sel: '.o_field_widget[name=td_workcenter_id]' },
              { name: 'downtime_hours', sel: '.o_field_widget[name=td_downtime_hours]' }] },
    // F-61 — табель цеху з кіоску за PIN: файл для BAS (імітація)
    { n: 45, role: 'fin', url: '/odoo/action-td_mebli_attendance.td_mebli_timesheet_export_action', name: 'timesheet-bas',
      act: async (c, { press }) => {
          await press(c, c.page.locator('.modal button[name=action_build]')); await c.page.waitForTimeout(800);
          await c.page.locator('.modal .modal-title').first().click(); await c.page.waitForTimeout(300);  // поле дати не в фокусі
      },
      facts: [{ name: 'total_hours', sel: '.modal .o_field_widget[name=total_hours]' }] },
    // F-61 — стандартний кіоск «Відвідування» з PIN
    { n: 46, role: 'fin', url: `/hr_attendance/${W2.kiosk_key || 'none'}`, name: 'kiosk',
      facts: [] },
    // F-64 — ранковий брифінг власника у «Вхідних» (шаблон за даними, без AI)
    { n: 47, role: 'owner', url: '/odoo/discuss', name: 'briefing',
      act: async (c, { press }) => {
          await press(c, c.page.locator('.o-mail-DiscussSidebar-item, button, a', { hasText: 'Вхідні' }).first());
          await c.page.waitForTimeout(1500);
      },
      facts: [{ name: 'at_risk', sel: '.o-mail-Message .td_briefing, .o-mail-Message-body', re: 'під загрозою: \\d+' }] },
    // F-65 — табло цеху на ТВ
    { n: 48, role: 'chief', url: '/odoo/action-td_mebli_dashboard.action_shop_board', name: 'shop-board',
      facts: [{ name: 'done', sel: '.td_k_board_done .td_value' }, { name: 'risk', sel: '.td_k_board_risk .td_value' }] },
    // F-57 (коробка B) — аналог матеріалу при дефіциті в компонентах МО
    { n: 49, role: 'tech', url: `/odoo/action-mrp.mrp_production_action/${W2.analog_mo || 0}`, name: 'analog',
      act: async (c, { press }) => { await press(c, tab(c, 'Компоненти')); },
      facts: [{ name: 'hint', sel: '.o_field_widget[name=move_raw_ids] td[name=td_analog_hint]:not(:empty)' }] },
];
// прохід 1 змінює дані (імпорт CSV, «Взято» з PIN); прохід 2 — лише читання, дашборд першим (recording.md); порядок ПОКАЗУ — SALES §6 (дашборд у кінці) — монтаж A-21c
// 22, 23 лише читають, але знімаються в проході 1: кліп M_act (прохід 1) підписує акт цього виїзду
export const PASS1 = [3, 5, 22, 23, 35];
export const PASS2 = [15, 16, 0, 1, 2, 17, 18, 19, 4, 6, 20, 7, 8, 9, 10, 11, 12, 13, 14, 21, 24, 25, 26, 27, 28, 29,
    48, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 49];
// scenario.mjs іде за порядком STEPS: прохід 1, потім прохід 2 (дашборд першим)
export const STEPS = [...PASS1, ...PASS2].map((n) => ALL.find((s) => s.n === n));
