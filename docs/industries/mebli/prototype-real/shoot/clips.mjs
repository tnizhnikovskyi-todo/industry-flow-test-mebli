// Живі записи зрізу A-21 (спроба 2), ПОВНИЙ ОБСЯГ — кроки кліпів підготувала хвиля 1, знімає хвиля 2 (PLAN.md §6). Титри — лише події (бренд — A-21c).
// Порядок показу — SALES §6 (запис 36): сцена 4 (D_late, екран прийнятого зразка) першою, D_dashboard — останнім; порядок ЗЙОМКИ — PASS1, потім PASS2 (дашборд першим).
import { clip, title, titleOff, hold, zoom, zoomOff, settle, press, typeIn, glide, focus, scrollTo, fact, goto } from './rec_lib.mjs';
const ORDER = process.env.ORDER_ID || '123';
const tab = (c, text) => c.page.locator('.o_notebook_headers a', { hasText: text });
const row = (c, text) => c.page.locator('.o_data_row, .o_kanban_record', { hasText: text });
const btn = (c, text) => c.page.locator('button', { hasText: text });
const CSV = new URL('./data/kitchen-spec.csv', import.meta.url).pathname;

export const PASS1 = ['D_csv', 'D_tablet', 'M_tablet', 'D_kit', 'D_cutting', 'M_act'];
// прохід 2 — дашборд першим (recording.md, після fix_dates); D_sample (прийнятий зразок) НЕ перезнімається — сцена 4 повного обсягу = D_late
// мобільні кліпи (хвиля 3, 390×844, isMobile, hasTouch, DPR 3): M_tablet і M_act змінюють дані (прохід 1), решта — лише читання
export const PASS2 = ['D_dashboard', 'M_dashboard', 'D_late', 'M_late', 'D_measure', 'M_measure', 'D_change', 'D_install', 'D_accruals', 'D_claims'];
const TABLET = '/odoo/action-td_mebli_shop.mrp_workorder_td_tablet_action';
const ACTS = '/odoo/action-td_mebli_install.td_mebli_install_act_action';
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
            await typeIn(c, c.page.locator('.o_searchview_input'), 'S00123/391'); await c.page.keyboard.press('Enter'); await settle(c.page, 700);
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
            // запит власника: деталі видно й у виробничому замовленні — вкладка «Деталі» (лише читання, підсумки на все МО)
            await goto(c, '/odoo/action-mrp.mrp_production_action');
            await typeIn(c, c.page.locator('.o_searchview_input'), 'WH/MO/00109'); await c.page.keyboard.press('Enter'); await settle(c.page, 700);
            await press(c, row(c, 'WH/MO/00109').locator('td[name=name]'));
            await press(c, tab(c, 'Деталі'));
            await title(c, 'Виробниче замовлення', 'Ті самі деталі — **у вкладці «Деталі»** замовлення цеху');
            await focus(c, '.o_field_widget[name=td_part_ids]'); await hold(c, 3000); await titleOff(c);
            await fact(c.page, 'D_csv', 'mo_part_count', '.o_field_widget[name=td_part_count]');
        });
    },
    // сцена 3 — зміна фасадів (B)
    async D_change() {
        return clip('D_change', { role: 'salon', url: `/odoo/action-sale.action_orders/${ORDER}` }, async (c) => {
            await settle(c.page, 900); c.mark();
            await press(c, tab(c, 'Зміни'));
            await title(c, 'Зміна від клієнта', 'Нова версія: **ціна й дата** з причиною «Клієнт»');
            await focus(c, '.o_data_row'); await zoom(c, '.o_data_row', 1.4, 900); await hold(c, 3500); await zoomOff(c); await hold(c, 800); await titleOff(c);
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
            // кіоск: працівник — зі списку (на телефоні пошуковий діалог співробітників недоступний ролі планшета)
            await press(c, c.page.locator('.modal .o_field_widget[name=employee_id] input'));
            await press(c, c.page.locator('.o_select_menu_item', { hasText: 'Петро Гуменюк' })); await settle(c.page, 400);
            await typeIn(c, c.page.locator('.modal .o_field_widget[name=pin] input'), '1111');
            await press(c, btn(c, 'Підтвердити'));
            await hold(c, 1500); await titleOff(c);
            // запит власника: деталі завдання — тут же, кнопкою «Деталі» (діалог лише читання)
            await press(c, c.page.locator('.o_data_row', { hasText: 'WH/MO/00110' }).locator('button', { hasText: 'Деталі' }).first());
            await title(c, 'Деталі завдання', 'Деталь, матеріал, кількість, **Д×Ш і кромка** — у планшеті');
            await focus(c, '.modal .o_field_widget[name=td_part_ids]'); await hold(c, 3000); await titleOff(c);
            await fact(c.page, 'D_tablet', 'part_count', '.modal .o_field_widget[name=td_part_count]');
            await press(c, c.page.locator('.modal-footer button', { hasText: 'Закрити' }));
            await hold(c, 800);
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
    // сцена 5а — пакет розкрою за декором (змінює дані: нове завдання з двох МО замовлення показу) і ділові обрізки;
    // результат оптимізатора-імітації в кадр не йде (OUT-02): завдання лишається чернеткою, вкладка «Деталі»
    async D_cutting() {
        return clip('D_cutting', { role: 'tech', url: '/odoo/action-mrp.mrp_production_action' }, async (c) => {
            await settle(c.page, 900); c.mark();
            await title(c, 'Розкрій пакетом', 'Кілька виробничих замовлень одного декору — **одне завдання розкрою**');
            await typeIn(c, c.page.locator('.o_searchview_input'), 'S00123'); await c.page.keyboard.press('Enter'); await settle(c.page, 700);
            await press(c, c.page.locator('thead .o_list_record_selector input'));
            await press(c, c.page.locator('.o_cp_action_menus button, .o_control_panel_actions .dropdown-toggle', { hasText: 'Дії' }).first());
            await press(c, c.page.locator('.o-dropdown-item, .dropdown-item', { hasText: 'Створити завдання розкрою' }));
            await settle(c.page, 900);
            await press(c, tab(c, 'Деталі'));
            await focus(c, '.o_field_widget[name=production_ids]'); await hold(c, 2500); await titleOff(c);
            await fact(c.page, 'D_cutting', 'job_orders', '.o_field_widget[name=production_ids]');
            await c.page.goto(c.page.url().split('/odoo')[0] + '/odoo/action-td_mebli_cutting.stock_lot_td_offcut_action');
            await settle(c.page, 900);
            await title(c, 'Ділові обрізки', 'Залишок листа — **в облік за декором**, а не у відходи');
            await focus(c, '.o_list_renderer'); await hold(c, 3000); await titleOff(c);
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
            await focus(c, '.o_list_renderer'); await hold(c, 2000);
            await typeIn(c, c.page.locator('.o_searchview_input'), 'АКТ-0002'); await c.page.keyboard.press('Enter'); await settle(c.page, 700);
            await press(c, row(c, 'АКТ-0002').locator('td[name=name]'));
            await settle(c.page, 900);
            await focus(c, '.o_field_widget[name=defect_ids]'); await hold(c, 2500);
            await focus(c, '.o_field_widget[name=crew_amount]'); await hold(c, 2000); await titleOff(c);
            await fact(c.page, 'D_install', 'crew_amount', '.o_field_widget[name=crew_amount]');
        });
    },
    async D_accruals() {
        return clip('D_accruals', { role: 'fin', url: '/odoo/action-td_mebli_install.td_mebli_accrual_action' }, async (c) => {
            await settle(c.page, 900); c.mark();
            await title(c, 'Нарахування', 'Відрядна, % бригаді, **премії й штрафи з причиною**');
            await hold(c, 2500);
            await press(c, c.page.locator('.o_switch_view.o_list'));
            await settle(c.page, 700);
            await press(c, c.page.locator('.o_searchview_dropdown_toggler').first());
            await press(c, c.page.locator('.o-dropdown-item, .dropdown-item', { hasText: 'Вид' }));
            await c.page.keyboard.press('Escape'); await settle(c.page, 600);
            await press(c, c.page.locator('.o_group_header', { hasText: 'Відрядна' }));
            await title(c, 'Відрядна за операцію', 'Розцінка операції × деталі чи метри кромки — **не години × ставка**');
            await focus(c, '.o_data_row td[name=piece_rate]'); await hold(c, 3000);
            await press(c, c.page.locator('.o_group_header', { hasText: 'Штраф' }));
            await focus(c, '.o_data_row.text-danger'); await hold(c, 2500); await titleOff(c);
            await fact(c.page, 'D_accruals', 'piece_rate', '.o_data_row td[name=piece_rate]');
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
            await press(c, c.page.locator('.td_card.td_k_margin .td_value'));
            await settle(c.page, 900);
            await title(c, 'Картка = звіт', 'Ті самі замовлення й та сама **зважена маржа**');
            await focus(c, 'tfoot'); await hold(c, 3000); await titleOff(c);
            await fact(c.page, 'D_dashboard', 'drill_orders', '.o_pager_limit');
        });
    },

    // ---------------- телефон (хвиля 3) ----------------
    // сцена 1 — замірник на телефоні: ніші, техніка «не вміщається», фото ніш і комунікацій
    async M_measure() {
        return clip('M_measure', { role: 'measure', mobile: true, url: '/odoo/action-td_mebli_measure.td_mebli_measure_action' }, async (c) => {
            await settle(c.page, 900); c.mark();
            await title(c, 'Замірник з телефона', 'Замір-лист **на об\'єкті**, а не на папері');
            await hold(c, 1200);
            await press(c, row(c, 'Кухня й передпокій').locator('td').first());
            await press(c, tab(c, 'Техніка клієнта'));
            await scrollTo(c, '.o_data_row.text-danger');
            await title(c, 'Не вміщається', 'Холодильник **глибший за нішу** — видно до виробництва');
            await focus(c, '.o_data_row.text-danger'); await hold(c, 2500);
            await fact(c.page, 'M_measure', 'issue', '.alert-danger .o_field_widget[name=issue_text]');
            await press(c, tab(c, 'Комунікації й фото'));
            await scrollTo(c, '.o_field_widget[name=photo_ids]');
            await title(c, 'Фото ніш', 'Фото й комунікації — **у тому ж замір-листі**');
            await focus(c, '.o_field_widget[name=photo_ids]'); await hold(c, 2500); await titleOff(c);
        });
    },
    // сцена 5 — планшет цеху на телефоні: «Зроблено» за PIN (змінює дані: завершує робоче завдання, яке взяв D_tablet)
    async M_tablet() {
        return clip('M_tablet', { role: 'tablet', mobile: true, url: TABLET }, async (c) => {
            await settle(c.page, 900); c.mark();
            await title(c, 'Цех', '«Взято» і «Зроблено» — **за PIN працівника**');
            // на телефоні — картки канбану (N5): працівник і «Зроблено» в картці; робоче завдання, яке Петро взяв у D_tablet (WH/MO/00110)
            const r = c.page.locator('.o_kanban_record', { hasText: 'WH/MO/00110' }).filter({ has: c.page.locator('button', { hasText: 'Зроблено' }) }).first();
            await r.scrollIntoViewIfNeeded(); await settle(c.page, 300);
            await r.evaluate((e) => e.classList.add('td_shot_focus')); await focus(c, '.td_shot_focus'); await hold(c, 1800);
            // запит власника: деталі завдання на телефоні — кнопкою в картці (діалог з картками деталей), без зламу канбану
            await press(c, r.locator('button.td_parts_link'));
            await title(c, 'Деталі', 'Що різати: **розміри й кромка** — у картці завдання');
            await hold(c, 2600); await titleOff(c);
            await press(c, c.page.locator('.modal-footer button', { hasText: 'Закрити' })); await settle(c.page, 500);
            await r.scrollIntoViewIfNeeded();
            await press(c, r.locator('button', { hasText: 'Зроблено' }));
            // кіоск: працівник — зі списку (на телефоні пошуковий діалог співробітників недоступний ролі планшета)
            await press(c, c.page.locator('.modal .o_field_widget[name=employee_id] input'));
            await press(c, c.page.locator('.o_select_menu_item', { hasText: 'Петро Гуменюк' })); await settle(c.page, 400);
            await typeIn(c, c.page.locator('.modal .o_field_widget[name=pin] input'), '1111');
            await press(c, btn(c, 'Підтвердити'));
            await settle(c.page, 900);
            await title(c, 'Зроблено', 'Час і виконавця записано — **основа відрядної**');
            await hold(c, 2000); await titleOff(c);
            await fact(c.page, 'M_tablet', 'cut_queue', '.o_kanban_group:has(.o_column_title:has-text("Розкрій")) .o_column_title', { re: '(?<=\\()\\d+' });
        });
    },
    // сцена 6 — бригадир на телефоні: акт з фото, підпис клієнта пальцем (змінює дані: акт підписано)
    async M_act() {
        return clip('M_act', { role: 'fitter', mobile: true, url: ACTS }, async (c) => {
            await settle(c.page, 900); c.mark();
            await title(c, 'Монтажник', 'Акт — **на телефоні**, на об\'єкті клієнта');
            const draft = c.page.locator('.o_data_row, .o_kanban_record').filter({ hasText: 'Фінальний' }).filter({ hasText: 'Чернетка' }).first();
            await press(c, draft.locator('td').first());
            await press(c, tab(c, 'Фото й чек-лист'));
            await scrollTo(c, '.o_field_widget[name=photo_ids]');
            await title(c, 'Фото', 'Фото після монтажу — **в акті**, а не в месенджері');
            await focus(c, '.o_field_widget[name=photo_ids]'); await hold(c, 2200);
            await press(c, tab(c, 'Підпис'));
            await scrollTo(c, '.o_field_widget[name=signature]');
            await press(c, c.page.locator('.o_field_widget[name=signature] .o_signature').first());
            await settle(c.page, 700);
            await title(c, 'Підпис клієнта', 'Пальцем на екрані — **акт підписано**');
            const cv = c.page.locator('.modal canvas').first();
            const b = await cv.boundingBox();
            const pts = [[.12, .62], [.2, .3], [.28, .7], [.36, .35], [.45, .65], [.55, .4], [.62, .6], [.72, .32], [.86, .58]];
            await c.page.mouse.move(b.x + b.width * pts[0][0], b.y + b.height * pts[0][1]); await c.page.mouse.down();
            for (const [px, py] of pts.slice(1)) await c.page.mouse.move(b.x + b.width * px, b.y + b.height * py, { steps: 8 });
            await c.page.mouse.up(); await hold(c, 900);
            await press(c, c.page.locator('.modal-footer button', { hasText: 'Прийняти' }));
            await settle(c.page, 700);
            const save = c.page.locator('.o_form_button_save:visible');
            if (await save.count()) await press(c, save.first());
            // на телефоні панель керування липка: кнопку статусу докручуємо нижче неї, інакше дотик влучить у «Новий»
            await scrollTo(c, '.o_form_statusbar', 900, 0.35); await settle(c.page, 500);
            await press(c, c.page.locator('.o_form_statusbar button[name=action_sign]'));
            await settle(c.page, 1000);
            await scrollTo(c, '.o_statusbar_status', 900, 0.35);
            await focus(c, '.o_statusbar_status'); await hold(c, 2200); await titleOff(c);
            await fact(c.page, 'M_act', 'act_state', '.o_statusbar_status .o_arrow_button_current');
            await fact(c.page, 'M_act', 'crew_amount', '.o_field_widget[name=crew_amount]');
        });
    },
    // сцена 4 на телефоні — менеджер салону бачить зсув дати (лише читання)
    async M_late() {
        return clip('M_late', { role: 'salon', mobile: true, url: `/odoo/action-sale.action_orders/${ORDER}` }, async (c) => {
            await settle(c.page, 900); c.mark();
            await title(c, 'Менеджер у салоні', 'Дата під загрозою — **видно з телефона**');
            await focus(c, '.td_date_alert'); await hold(c, 2200);
            await scrollTo(c, '.o_field_widget[name=td_forecast_date]');
            await focus(c, '.o_field_widget[name=td_forecast_date]'); await hold(c, 2200); await titleOff(c);
            await fact(c.page, 'M_late', 'forecast_date', '.o_field_widget[name=td_forecast_date]');
        });
    },
    // сцена 8 на телефоні — дашборд керівника: картки одна під одною, картка маржі -> записи, які вона порахувала
    async M_dashboard() {
        return clip('M_dashboard', { role: 'owner', mobile: true, url: '/odoo/action-td_mebli_dashboard.action_dashboard' }, async (c) => {
            await settle(c.page, 1200); c.mark();
            await title(c, 'Власник', 'Фабрика — **у телефоні**');
            await fact(c.page, 'M_dashboard', 'margin', '.td_card.td_k_margin .td_value');
            await fact(c.page, 'M_dashboard', 'revenue', '.td_card.td_k_margin', { re: '(?<=виручки )[\\d\\s\u00a0\u202f]+\\S' });
            await hold(c, 1800);
            for (const k of ['td_k_on_time', 'td_k_margin', 'td_k_claims', 'td_k_load']) {
                if (await c.page.locator(`.td_card.${k}`).count()) { await scrollTo(c, `.td_card.${k}`, 900, 0.12); await hold(c, 1300); }
            }
            await scrollTo(c, '.td_card.td_k_margin', 900, 0.12);
            await press(c, c.page.locator('.td_card.td_k_margin .td_label'));
            await settle(c.page, 900);
            await title(c, 'Картка = звіт', 'Ті самі замовлення, що й у картці');
            await scrollTo(c, 'tfoot', 900, 0.5); await focus(c, 'tfoot');
            await hold(c, 2500); await titleOff(c);
            // на телефоні пейджер без лічильника: картку звіряємо з підсумком виручки звіту (DASH-drill)
            await fact(c.page, 'M_dashboard', 'drill_revenue', 'tfoot', { re: '[\\d\u00a0\u202f ]+,\\d\\d' });
        });
    },
};
