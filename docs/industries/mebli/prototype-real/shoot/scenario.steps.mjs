// Кроки десктопного сценарію зрізу A-21 (спроба 2), ПОВНИЙ ОБСЯГ — хвиля 1 підготувала, знімає хвиля 2 (PLAN.md §1 «Повний обсяг», §6).
// Порядок — SALES §6 за записом 36: крок 0 (прийнятий зразок, S-02, сцена 4) першим; дашборд S-19 — останнім.
// Замовлення показу S00123 — env ORDER_ID (типово 123: id замовлення з «Посиланням клієнта» «Кухня й шафа-купе, квартира»).
// Селектори не перевірені на живому записі: хвиля 2 звіряє їх на demo-mebli-full і правит лише цей файл.
const ORDER = process.env.ORDER_ID || '123';
const CSV = new URL('./data/kitchen-spec.csv', import.meta.url).pathname;
const row = (c, text) => c.page.locator('.o_data_row', { hasText: text });
const tab = (c, text) => c.page.locator('.o_notebook_headers a', { hasText: text });
const btn = (c, text) => c.page.locator('button', { hasText: text });

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
          await press(c, c.page.locator('.o_select_menu_item', { hasText: 'Петро Гуменюк' })); await c.page.waitForTimeout(400);
          await typeIn(c, c.page.locator('.modal .o_field_widget[name=pin] input'), '1111');
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
          { name: 'revenue_total', sel: 'tfoot td:nth-child(2)' },
          { name: 'plan_cost_total', sel: 'tfoot td:nth-child(3)' },
      ] },
    // сцена 2 — пропозиція до підтвердження: маржа видно ДО запуску (не 100 %: планова собівартість у чернетці)
    { n: 17, role: 'salon', url: '/odoo/action-sale.action_quotations/117', name: 'quotation-margin',
      facts: [
          { name: 'state', sel: '.o_statusbar_status .o_arrow_button_current' },
          { name: 'margin_percent', sel: '.o_field_widget[name=margin_percent]', re: '[\\d,.]+\\s*%' },
      ] },
];
// прохід 1 змінює дані (імпорт CSV, «Взято» з PIN); прохід 2 — лише читання, дашборд першим (recording.md); порядок ПОКАЗУ — SALES §6 (дашборд у кінці) — монтаж A-21c
export const PASS1 = [3, 5];
export const PASS2 = [15, 16, 0, 1, 2, 17, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14];
// scenario.mjs іде за порядком STEPS: прохід 1, потім прохід 2 (дашборд першим)
export const STEPS = [...PASS1, ...PASS2].map((n) => ALL.find((s) => s.n === n));
