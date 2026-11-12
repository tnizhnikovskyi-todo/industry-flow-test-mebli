// Живі записи зрізу A-21 (спроба 2), ПОВНИЙ ОБСЯГ — кроки кліпів підготувала хвиля 1, знімає хвиля 2 (PLAN.md §6). Титри — лише події (бренд — A-21c).
// Порядок показу — SALES §6 (запис 36): сцена 4 (D_late, екран прийнятого зразка) першою, D_dashboard — останнім; порядок ЗЙОМКИ — PASS1, потім PASS2 (дашборд першим).
import { clip, title, titleOff, hold, zoom, zoomOff, settle, press, typeIn, glide, focus, scrollTo, fact } from './rec_lib.mjs';
const ORDER = process.env.ORDER_ID || '123';
const tab = (c, text) => c.page.locator('.o_notebook_headers a', { hasText: text });
const row = (c, text) => c.page.locator('.o_data_row, .o_kanban_record', { hasText: text });
const btn = (c, text) => c.page.locator('button', { hasText: text });
const CSV = new URL('./data/kitchen-spec.csv', import.meta.url).pathname;

export const PASS1 = ['D_csv', 'D_tablet', 'D_kit'];
// прохід 2 — дашборд першим (recording.md, після fix_dates); D_sample (прийнятий зразок) НЕ перезнімається — сцена 4 повного обсягу = D_late
export const PASS2 = ['D_dashboard', 'D_late', 'D_measure', 'D_change', 'D_cutting', 'D_install', 'D_accruals', 'D_claims'];
export const CLIPS = {
    // сцена 4 — екран прийнятого зразка як є (нові кнопки S-02 у кадрі; D_sample не перезнімається — PLAN §7)
    async D_late() {
        return clip('D_late', { role: 'salon', url: `/odoo/action-sale.action_orders/${ORDER}` }, async (c) => {
            await settle(c.page, 900);
            await fact(c.page, 'D_late', 'margin_percent', '.o_field_widget[name=margin_percent]', { re: '[\\d,.]+\\s*%' });
            c.mark();
            await title(c, 'Менеджер продажу', 'Обіцяли клієнту дату — система **вже бачить**, що її зірве');
            await hold(c, 1500);
            await focus(c, '.td_date_alert');
            await glide(c, 520, 120, 600);
            await hold(c, 2000);
            await zoom(c, '.o_group .o_field_widget[name=td_forecast_date]', 1.7, 900);
            await focus(c, '.o_group .o_field_widget[name=td_forecast_date]');
            await hold(c, 1900);
            await zoomOff(c);
            await titleOff(c);
            await press(c, tab(c, 'Закупівлі під замовлення'));
            await scrollTo(c, '.o_data_row.text-danger');
            await title(c, 'Причина зсуву', 'Фасади: дата постачальника в закупівлі — **пізніше на 2 тижні**');
            await zoom(c, '.o_data_row.text-danger', 1.5, 900);
            await focus(c, '.o_data_row.text-danger');
            await hold(c, 3500);
            await zoomOff(c);
            await hold(c, 800);
            await fact(c.page, 'D_late', 'delay_days', '.o_group .o_field_widget[name=td_delay_days]', { re: '\\d+' });
            await fact(c.page, 'D_late', 'late_item_ready', '.o_data_row.text-danger td[name=td_date_ready]');
        });
    },
    // сцена 1 — замір: холодильник глибший за нішу
    async D_measure() {
        return clip('D_measure', { role: 'measure', url: '/odoo/action-td_mebli_measure.td_mebli_measure_action' }, async (c) => {
            await settle(c.page, 900); c.mark();
            await title(c, 'Замірник', 'Ніші й техніка клієнта — **у картці замовлення**');
            await press(c, row(c, 'Кухня й передпокій').locator('td[name=name]'));
            await press(c, tab(c, 'Техніка клієнта'));
            await focus(c, '.o_data_row.text-danger');
            await zoom(c, '.o_data_row.text-danger', 1.5, 900);
            await title(c, 'Помилку видно до виробництва', 'Холодильник **глибший за нішу** на 30 мм');
            await hold(c, 3000); await zoomOff(c); await titleOff(c);
            await fact(c.page, 'D_measure', 'fridge_check', '.o_data_row.text-danger td[name=issue]');
        });
    },
    // сцена 2 — імпорт CSV з розпізнаванням колонок (змінює дані)
    async D_csv() {
        return clip('D_csv', { role: 'tech', url: '/odoo/action-mrp.mrp_bom_form_action' }, async (c) => {
            await settle(c.page, 900); c.mark();
            await title(c, 'Технолог', 'Специфікація з програми проєктування — **без ручного перенесення**');
            await press(c, row(c, 'S00123/391').locator('td').nth(1));
            await press(c, c.page.locator('.o_cp_action_menus .dropdown-toggle').first());
            await press(c, c.page.locator('.dropdown-item', { hasText: 'Імпорт деталей' }));
            await c.page.locator('.modal input[type=file]').setInputFiles(CSV);
            await press(c, btn(c, 'Розпізнати колонки'));
            await focus(c, '.modal .o_field_widget[name=mapping]'); await hold(c, 2500);
            await press(c, c.page.locator('.modal-footer button', { hasText: 'Імпортувати' }));
            await settle(c.page, 900);
            await press(c, tab(c, 'Деталі'));
            await title(c, 'Деталі в специфікації', 'Розміри, матеріал і кромка — **з файла, без ручного вводу**');
            await focus(c, '.o_field_widget[name=td_part_ids]'); await hold(c, 3000); await titleOff(c);
            await fact(c.page, 'D_csv', 'part_count', '.o_field_widget[name=td_part_count]');
        });
    },
    // сцена 3 — зміна фасадів (B)
    async D_change() {
        return clip('D_change', { role: 'salon', url: `/odoo/action-sale.action_orders/${ORDER}` }, async (c) => {
            await settle(c.page, 900); c.mark();
            await press(c, tab(c, 'Зміни'));
            await title(c, 'Зміна від клієнта', 'Нова версія: **ціна й дата** з причиною «Клієнт»');
            await focus(c, '.o_data_row'); await hold(c, 3000); await titleOff(c);
            await fact(c.page, 'D_change', 'shift_days', '.o_data_row td[name=shift_days]');
        });
    },
    // сцена 5 — планшет цеху за PIN (змінює дані)
    async D_tablet() {
        return clip('D_tablet', { role: 'tablet', url: '/odoo/action-td_mebli_shop.mrp_workorder_td_tablet_action' }, async (c) => {
            await settle(c.page, 900); c.mark();
            await title(c, 'Цех', '«Взято» — **за PIN працівника**, без окремого користувача');
            await press(c, c.page.locator('.o_group_header', { hasText: 'Розкрій' }));
            await press(c, c.page.locator('.o_data_row', { hasText: 'WH/MO/00110' }).locator('button', { hasText: 'Взято' }));
            await typeIn(c, c.page.locator('.modal .o_field_widget[name=employee_id] input'), 'Петро');
            await press(c, c.page.locator('.o-autocomplete--dropdown-item').first());
            await typeIn(c, c.page.locator('.modal .o_field_widget[name=pin] input'), '1111');
            await press(c, btn(c, 'Підтвердити'));
            await hold(c, 2000); await titleOff(c);
        });
    },
    // сцена 5 — неповний комплект не відвантажується (змінює дані: спроба відвантажити)
    async D_kit() {
        return clip('D_kit', { role: 'store', url: '/odoo/action-td_mebli_shop.td_mebli_kit_line_action' }, async (c) => {
            await settle(c.page, 900); c.mark();
            await title(c, 'Комірник', 'Комплектувальний лист: **що в яке місце**');
            await hold(c, 2000);
            await press(c, c.page.locator('.o_searchview_facet .o_facet_remove').first());
            await press(c, c.page.locator('.o_searchview_dropdown_toggler').first());
            await press(c, c.page.locator('.o-dropdown-item, .dropdown-item', { hasText: 'Не запаковано' }));
            await c.page.keyboard.press('Escape'); await settle(c.page, 600);
            await title(c, 'Не запаковано', 'Без **задньої стінки** комплект не відвантажиться');
            await focus(c, '.o_data_row.text-danger'); await hold(c, 3000); await titleOff(c);
            await fact(c.page, 'D_kit', 'missing_part', '.o_data_row.text-danger', { re: 'Задня стінка[^0-9]*' });
        });
    },
    // сцена 5а — пакет розкрою і ділові обрізки (без оптимізатора, OUT-02)
    async D_cutting() {
        return clip('D_cutting', { role: 'tech', url: '/odoo/action-td_mebli_cutting.td_mebli_cutting_job_action' }, async (c) => {
            await settle(c.page, 900); c.mark();
            await title(c, 'Розкрій пакетом', 'Кілька замовлень одного декору — **одне завдання**, обрізки в облік');
            await press(c, c.page.locator('.o_data_row').first());
            await hold(c, 3000); await titleOff(c);
        });
    },
    // сцена 6 — монтаж: календар, акт з недоліком і % бригаді
    async D_install() {
        return clip('D_install', { role: 'fitter', url: '/odoo/action-td_mebli_install.td_mebli_install_calendar_action' }, async (c) => {
            await settle(c.page, 900); c.mark();
            await title(c, 'Монтаж', 'Два виїзди: **корпуси → стільниця**');
            await hold(c, 2500);
            await c.page.goto(c.page.url().split('/odoo')[0] + '/odoo/action-td_mebli_install.td_mebli_install_act_action');
            await settle(c.page, 900);
            await title(c, 'Акт', 'Фото, недолік, підпис клієнта — **% бригаді рахується з акта**');
            await focus(c, '.o_list_renderer'); await hold(c, 3000); await titleOff(c);
        });
    },
    async D_accruals() {
        return clip('D_accruals', { role: 'fin', url: '/odoo/action-td_mebli_install.td_mebli_accrual_action' }, async (c) => {
            await settle(c.page, 900); c.mark();
            await title(c, 'Нарахування', 'Відрядна, % бригаді, **премії й штрафи з причиною**');
            await hold(c, 3500); await titleOff(c);
        });
    },
    // сцена 7 — рекламації і план ↔ факт
    async D_claims() {
        return clip('D_claims', { role: 'chief', url: '/odoo/action-td_mebli_claim.td_mebli_claim_action' }, async (c) => {
            await settle(c.page, 900); c.mark();
            await title(c, 'Рекламації', 'Кожна — з причиною, строком і **хто платить**');
            await focus(c, '.o_kanban_record .text-bg-danger'); await hold(c, 3000); await titleOff(c);
            await c.page.goto(c.page.url().split('/odoo')[0] + '/odoo/action-td_mebli_cost.sale_order_td_cost_fact_action');
            await settle(c.page, 900);
            await title(c, 'Собівартість', 'План ↔ факт **по кожному замовленню**');
            await hold(c, 3000); await titleOff(c);
        });
    },
    // сцена 8 — дашборд керівника (останнім); картка маржі -> drill-down
    async D_dashboard() {
        return clip('D_dashboard', { role: 'owner', url: '/odoo/action-td_mebli_dashboard.action_dashboard' }, async (c) => {
            await settle(c.page, 1200); c.mark();
            await title(c, 'Власник', 'Фабрика **на одному екрані**');
            await fact(c.page, 'D_dashboard', 'margin', '.td_card.td_k_margin .td_value');
            await fact(c.page, 'D_dashboard', 'margin_orders', '.td_card.td_k_margin', { re: '(?<=замовлень )\\d+' });
            await hold(c, 3000);
            await zoom(c, '.td_card.td_k_shift', 1.5, 900); await hold(c, 2500); await zoomOff(c);
            await press(c, c.page.locator('.td_card.td_k_margin'));
            await settle(c.page, 900);
            await title(c, 'Картка = звіт', 'Ті самі замовлення й та сама **зважена маржа**');
            await focus(c, 'tfoot'); await hold(c, 3000); await titleOff(c);
            await fact(c.page, 'D_dashboard', 'drill_orders', '.o_pager_limit');
        });
    },
};
