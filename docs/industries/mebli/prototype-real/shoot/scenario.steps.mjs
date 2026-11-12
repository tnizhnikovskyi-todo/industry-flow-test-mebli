// Кроки десктопного сценарію зрізу A-21 (спроба 2). ЗРАЗОК: лише крок 0 — екран S-02 «Замовлення клієнта» з обіцяною й прогнозною датою
// і закупівлями під замовлення (F-23, F-31, NG-01; закупівлі — стандарт MTO + «Купити», лише читання: менеджер салону без групи
// «Закупівлі», читає закупівлі своїх замовлень за правилом доступу td_mebli_sale, смарт-кнопка «Купівлі» — лише закупівельникам; SALES §6 сцена 4, варіант цінності 1 SALES §4). Повний перелік кроків — після приймання зразка (PLAN.md §6).
// Замовлення показу шукається за полем «Посилання клієнта» (seed td_mebli_demo/dates.py), ідентифікатор — env ORDER_ID (типово 123).
const ORDER = process.env.ORDER_ID || '123';
export const STEPS = [
    { n: 0, role: 'salon', url: `/odoo/action-sale.action_orders/${ORDER}`, name: 'sample',
      act: async (c, { press }) => {
          await press(c, c.page.locator('.o_notebook_headers a', { hasText: 'Закупівлі під замовлення' }));
      },
      facts: [
          { name: 'promised_date', sel: '.o_field_widget[name=commitment_date]' },
          { name: 'forecast_date', sel: '.o_field_widget[name=td_forecast_date]' },
          { name: 'delay_days', sel: '.o_group .o_field_widget[name=td_delay_days]', re: '\\d+' },
          { name: 'late_item', sel: '.td_date_alert .o_field_widget[name=td_late_item]' },
          { name: 'late_item_supplier_date', sel: '.o_data_row.text-danger td[name=date_planned]' },
          { name: 'late_item_ready', sel: '.o_data_row.text-danger td[name=td_date_ready]' },
          { name: 'late_purchase', sel: '.o_data_row.text-danger td[name=order_id]' },
      ] },
];
export const PASS1 = [];
export const PASS2 = [0];
