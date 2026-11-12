// Мобільні кроки ролей (390×844, isMobile, hasTouch, DPR 3) зрізу A-21, повний обсяг — знімає хвиля 3 (PLAN.md §6). Скриншоти screens-mobile/mN-*.png, record: false.
// Ролі на телефоні: замірник (S-15, замір-лист з фото), планшет цеху (S-06), бригадир монтажу (S-12, акт з фото й підписом), менеджер салону (S-02), власник (S-19).
// Усі кроки лише читають (PASS2, після fix_dates і мобільних кліпів проходу 1: M_tablet «Зроблено», M_act підпис акта).
const ORDER = process.env.ORDER_ID || '123';
const row = (c, text) => c.page.locator('.o_kanban_record, .o_data_row', { hasText: text });
const tab = (c, text) => c.page.locator('.o_notebook_headers a', { hasText: text });

export const STEPS = [
    { n: 1, role: 'measure', url: '/odoo/action-td_mebli_measure.td_mebli_measure_action', name: 'measure',
      act: async (c, { press }) => { await press(c, row(c, 'Кухня й передпокій').locator('td').first()); await press(c, tab(c, 'Техніка клієнта')); },
      facts: [{ name: 'issue', sel: '.alert-danger .o_field_widget[name=issue_text]' }] },
    { n: 2, role: 'tablet', url: '/odoo/action-td_mebli_shop.mrp_workorder_td_tablet_action', name: 'tablet',
      // на телефоні планшет — картки (канбан, mobile_view_mode): працівник і кнопки видно без горизонтальної прокрутки (N5)
      act: async (c) => { await c.page.locator('.o_kanban_record', { hasText: 'WH/MO/00109' }).first().scrollIntoViewIfNeeded(); },
      facts: [{ name: 'cut_queue', sel: '.o_kanban_group:has(.o_column_title:has-text("Розкрій")) .o_column_title', re: '(?<=\\()\\d+' },
              { name: 'in_work', sel: '.o_kanban_record:has-text("WH/MO/00109") .td_workers' }] },
    { n: 3, role: 'fitter', url: '/odoo/action-td_mebli_install.td_mebli_install_act_action', name: 'act',
      act: async (c, { press }) => { await press(c, row(c, 'АКТ-0002').locator('td').first()); await press(c, tab(c, 'Фото й чек-лист')); },
      facts: [{ name: 'act_state', sel: '.o_statusbar_status .o_arrow_button_current' }] },
    { n: 4, role: 'salon', url: `/odoo/action-sale.action_orders/${ORDER}`, name: 'order',
      facts: [{ name: 'forecast_date', sel: '.o_field_widget[name=td_forecast_date]' }] },
    { n: 5, role: 'owner', url: '/odoo/action-td_mebli_dashboard.action_dashboard', name: 'dashboard',
      facts: [{ name: 'margin', sel: '.td_card.td_k_margin .td_value' }] },
];
export const PASS1 = [];
export const PASS2 = ['m1', 'm2', 'm3', 'm4', 'm5'];
