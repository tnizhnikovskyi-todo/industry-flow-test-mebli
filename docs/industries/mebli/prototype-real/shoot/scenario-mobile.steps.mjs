// Мобільні кроки ролей (390×844, isMobile) зрізу A-21, повний обсяг — підготувала хвиля 1, знімає хвиля 3 (PLAN.md §6).
// Ролі на телефоні: замірник (S-15), планшет цеху (S-06), бригадир монтажу (S-12, акт з підписом), менеджер салону (S-02), власник (S-19).
const ORDER = process.env.ORDER_ID || '123';
const row = (c, text) => c.page.locator('.o_kanban_record, .o_data_row', { hasText: text });
const tab = (c, text) => c.page.locator('.o_notebook_headers a', { hasText: text });

export const STEPS = [
    { n: 1, role: 'measure', url: '/odoo/action-td_mebli_measure.td_mebli_measure_action', name: 'measure',
      act: async (c, { press }) => { await press(c, row(c, 'Кухня й передпокій')); await press(c, tab(c, 'Техніка клієнта')); },
      facts: [{ name: 'issue', sel: '.alert-danger .o_field_widget[name=issue_text]' }] },
    { n: 2, role: 'tablet', url: '/odoo/action-td_mebli_shop.mrp_workorder_td_tablet_action', name: 'tablet',
      facts: [{ name: 'queue', sel: '.o_kanban_renderer, .o_list_renderer' }] },
    { n: 3, role: 'fitter', url: '/odoo/action-td_mebli_install.td_mebli_install_act_action', name: 'act',
      act: async (c, { press }) => { await press(c, row(c, 'Чернетка')); await press(c, tab(c, 'Підпис')); },
      facts: [{ name: 'act_state', sel: '.o_statusbar_status .o_arrow_button_current' }] },
    { n: 4, role: 'salon', url: `/odoo/action-sale.action_orders/${ORDER}`, name: 'order',
      facts: [{ name: 'forecast_date', sel: '.o_field_widget[name=td_forecast_date]' }] },
    { n: 5, role: 'owner', url: '/odoo/action-td_mebli_dashboard.action_dashboard', name: 'dashboard',
      facts: [{ name: 'margin', sel: '.td_card.td_k_margin .td_value' }] },
];
export const PASS1 = [];
export const PASS2 = ['m1', 'm2', 'm3', 'm4', 'm5'];
