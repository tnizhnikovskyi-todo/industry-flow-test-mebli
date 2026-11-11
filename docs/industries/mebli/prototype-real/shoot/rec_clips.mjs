// Живі записи екрана Odoo (десктоп 1600x900 -> 1920x1080 і телефон 390x640) для монтажу відео. Запуск: node rec_clips.mjs D_dash M_dash ...
// Кожен кліп = справжні кліки, набір тексту, прокрутка, zoom/pan, count-up; результат video/rec/<ім'я>.webm + .json. Порядок важливий: D_dash/M_dash
// знімаються першими — до того, як клипи підтверджують замовлення й змінюють цифри дашборда (щоб збігались зі скриншотами й SHOW.md).
import { focus, scrollTo, scrollAny, scrollN, pop, popOff, launch, clip, goto, glide, press, typeIn, title, titleOff, pain, hold, scroll, zoom, zoomOff, sleep, settle, BASE } from './rec_lib.mjs';

const DASH = '/odoo/action-td_mebli_dashboard.action_dashboard';
const card = (n) => `.td_dash_grid > .td_card:nth-child(${n})`;
const ev = (c, f, ...a) => c.page.evaluate(f, ...a);
const rpc = (c, model, method, args, kwargs = {}) => c.page.evaluate(async ([model, method, args, kwargs]) => {
    const r = await fetch(`/web/dataset/call_kw/${model}/${method}`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: { model, method, args, kwargs } }) });
    const j = await r.json(); if (j.error) throw new Error(j.error.data?.message || 'rpc'); return j.result;
}, [model, method, args, kwargs]);
const hideChatter = (c) => ev(c, () => { const s = document.createElement('style'); s.textContent = '.o-mail-Form-chatter, .o-mail-ChatterContainer{display:none!important}'; document.head.appendChild(s); });


// вибір значення в many2one: на десктопі випадний список, на телефоні — повноекранний діалог із картками
async function choose(c, input, text, pick) {
    const p = c.page; await press(c, input, { settleMs: 500 });
    if (!c.mobile) { await p.keyboard.press('Control+A'); await input.first().pressSequentially(text, { delay: 85 }); await sleep(600); await press(c, p.locator('ul.ui-autocomplete > li > a').filter({ hasText: pick || text }).first()); return; }
    await p.waitForSelector('.modal .o_kanban_record, .modal .o_data_row, .o-autocomplete--dropdown-item', { timeout: 8000 });
    if (await p.locator('.o-autocomplete--dropdown-item').count()) { await input.first().pressSequentially(text, { delay: 85 }); await sleep(600); await press(c, p.locator('.o-autocomplete--dropdown-item').filter({ hasText: pick || text }).first()); return; }
    const row = p.locator('.modal .o_kanban_record, .modal .o_data_row').filter({ hasText: pick || text });
    await press(c, (await row.count()) ? row.first() : p.locator('.modal .o_kanban_record, .modal .o_data_row').first());
}

const CLIPS = {
    // ---------------------------------------------------------------- керівник (десктоп)
    async D_dash() {
        return clip('D_dash', { role: 'owner', url: DASH }, async (c) => {
            await c.page.waitForSelector('.td_dash_grid .td_card'); await settle(c.page, 700);
            await ev(c, () => { window.__reveal('.td_card', 0); document.querySelectorAll('.td_card').forEach((e) => { e.style.opacity = '0'; }); });
            c.mark();
            await title(c, 'Власник · директор', 'Фабрика на одному екрані — **за 10 секунд**');
            await ev(c, () => { window.__reveal('.td_card', 170); window.__bars('.td_bar_fill', 1400); window.__countUp('.td_value', 1500); document.querySelectorAll('.td_line, .td_alert, .td_delta').forEach((e) => { e.style.transition = 'none'; e.style.opacity = '0'; setTimeout(() => { e.style.transition = 'opacity .5s'; e.style.opacity = '1'; }, 1700); }); });
            await hold(c, 2300);
            await title(c, 'Маржа', 'Середня маржа і **замовлення нижче 15 %** — червоним');
            await zoom(c, card(2), 1.8, 1000); await hold(c, 2300);
            await title(c, 'Дільниці', 'Понад 100 % — **вузьке місце**');
            await zoom(c, card(4), 1.7, 1000); await hold(c, 2300);
            await title(c, 'План / факт', 'Собівартість: план проти факту, відхід розкрою, економія з обрізків');
            await zoom(c, card(6), 1.7, 1000); await hold(c, 1800);
            await zoomOff(c, 800); await hold(c, 700);
            await title(c, 'Один клік', 'З картки — одразу в замовлення з низькою маржею');
            await press(c, c.page.locator(card(2)), { settleMs: 1500 });
            await hold(c, 2200);
        });
    },
    // ---------------------------------------------------------------- керівник (телефон)
    async M_dash() {
        return clip('M_dash', { role: 'owner', mobile: true, url: DASH }, async (c) => {
            const p = c.page;
            await c.page.waitForSelector('.td_dash_grid .td_card'); await settle(c.page, 700);
            await ev(c, () => { document.querySelectorAll('.td_card').forEach((e) => { e.style.opacity = '0'; }); });
            c.mark();
            await ev(c, () => { window.__reveal('.td_card', 220); window.__bars('.td_bar_fill', 1400); window.__countUp('.td_value', 1500); document.querySelectorAll('.td_line, .td_alert, .td_delta').forEach((e) => { e.style.transition = 'none'; e.style.opacity = '0'; setTimeout(() => { e.style.transition = 'opacity .5s'; e.style.opacity = '1'; }, 1700); }); });
            await title(c, 'Власник', 'Фабрика — **на екрані телефона**', null, { n: '2,77 млн ₴', l: 'виручка за місяць' });
            await hold(c, 2200);
            await zoom(c, card(1), 1.2, 800); await hold(c, 1700);
            await zoom(c, card(2), 1.2, 800); await title(c, 'Маржа', '**Низьку маржу** видно одразу', null, { n: '31,5 %', l: 'середня маржа; нижче 15 % — червоним' }); await hold(c, 700); await pop(c, card(2) + ' .td_value', 1.06); await focus(c, card(2) + ' .td_value'); await hold(c, 1300);
            await popOff(c, card(2) + ' .td_value'); await press(c, p.locator(card(2)), { settleMs: 1500 }); await title(c, 'Один тап', 'Тап — і **замовлення** з низькою маржею', null, { n: '7', l: 'замовлень із маржею нижче 15 %' }); await hold(c, 1700);
            await c.page.goBack(); await settle(c.page, 1800); await ev(c, () => { document.querySelectorAll('.td_card').forEach((e) => { e.style.opacity = '1'; }); });
            await zoomOff(c, 500); await scroll(c, '.td_dash', 330, 1300);
            await zoom(c, card(4), 1.2, 800); await title(c, 'Дільниці', 'Де **понад 100 %** — вузьке місце', null, { n: '129 %', l: 'Складання — вузьке місце' }); await hold(c, 900); await focus(c, card(4) + ' .td_bars'); await hold(c, 1300);
            await zoomOff(c, 500); await scroll(c, '.td_dash', 'end', 1500);
            await zoom(c, card(6), 1.2, 800); await title(c, 'План / факт', 'Собівартість: **план проти факту**', null, { n: '+0,6 %', l: 'факт проти плану' }); await hold(c, 900); await focus(c, card(6)); await hold(c, 1300);
        });
    },
    // ---------------------------------------------------------------- салон: замовлення з конфігуратором (десктоп)
    async D_sale() {
        return clip('D_sale', { role: 'salon', url: '/odoo/action-sale.action_quotations' }, async (c) => {
            const p = c.page; await settle(p, 1200);
            await press(c, p.locator('.o_list_button_add, .o-kanban-button-new').first());
            await typeIn(c, p.locator('.o_field_widget[name=partner_id] input'), 'Мороз', 40);
            await press(c, p.locator('ul.ui-autocomplete > li > a').first());
            await press(c, p.locator('.o_form_button_save'), { settleMs: 1200 });
            await hideChatter(c); c.mark();
            await pain(c, 'Менеджер салону', 'Покупець змінює декор — і **ціну рахують заново** на калькуляторі');
            await title(c, 'Салон', 'Замовлення збережено — додаємо виріб');
            await press(c, p.locator('a:has-text("Додати товар"), a:has-text("Add a product")').first());
            await typeIn(c, p.locator('div[name="product_template_id"] input'), 'Шафа-купе');
            await press(c, p.locator('ul.ui-autocomplete > li > a').filter({ hasText: /Шафа-купе/ }).first());
            await p.waitForSelector('.o_sale_product_configurator_dialog'); await settle(p, 900);
            const dlg = p.locator('.o_sale_product_configurator_dialog');
            const ptal = (label) => dlg.locator('div[name="ptal"]').filter({ has: p.locator('label', { hasText: label }) });
            await title(c, 'Конфігуратор', 'Декор, кромка, фурнітура — **ціна змінюється одразу**');
            await press(c, ptal('Декор корпусу').locator('span', { hasText: 'Дуб Сонома' }).first(), { settleMs: 900 });
            await press(c, ptal('Декор фасаду').locator('span', { hasText: 'Антрацит' }).first(), { settleMs: 900 });
            await press(c, ptal('Кромка').locator('span', { hasText: 'ПВХ 2 мм' }).first(), { settleMs: 900 });
            await press(c, ptal('Фурнітура').locator('span', { hasText: 'Преміум' }).first(), { settleMs: 900 });
            await title(c, 'Розміри', 'Вводимо **розміри покупця** — при ньому');
            for (const [label, value] of [['Ширина', '1800'], ['Висота', '2400'], ['Глибина', '600']]) {
                await typeIn(c, ptal(label).locator('input[type="text"]'), value, 110);
                await press(c, dlg.locator('.modal-body'), { settleMs: 700 });
            }
            await title(c, 'Ширше?', '«А якщо **трохи ширше**?» — вводимо 2000 мм');
            await typeIn(c, ptal('Ширина').locator('input[type="text"]'), '2000', 110);
            await press(c, dlg.locator('.modal-body'), { settleMs: 900 }); await hold(c, 900);
            await press(c, dlg.locator('button', { hasText: /Підтвердити|Confirm/ }), { settleMs: 1200 });
            await title(c, 'Ціна', 'Ціна перерахована за розмірами: **24 200 → 30 250 ₴**');
            await focus(c, '.o_data_row [name="price_subtotal"], .o_data_row'); await hold(c, 1400);
            await press(c, p.locator('.o_form_button_save'), { settleMs: 1200 });
            await hideChatter(c);
            // специфікація й собівартість будуються при збереженні рядка: чекаємо реальну маржу, а не 100 % до перерахунку
            await p.waitForFunction(() => !/\(100\s?%\)/.test(document.body.innerText) && /\d\d[,.]\d\d\s?%/.test(document.body.innerText), null, { timeout: 8000 }).catch(() => console.error('WARN D_sale: маржа в чернетці не перерахована'));
            await title(c, 'Маржа', 'Ціна й **маржа — ще в пропозиції**, до підтвердження');
            await press(c, p.locator('.o_optional_columns_dropdown_toggle').first(), { settleMs: 500 });
            for (const re of [/^\s*Маржа\s*$/, /^\s*Маржа \(%\)/]) {
                const box = p.locator('.o-dropdown--menu .dropdown-item').filter({ hasText: re }).first().locator('input[type=checkbox]');
                if ((await box.count()) && !(await box.isChecked())) await press(c, box, { settleMs: 700 });
            }
            await p.keyboard.press('Escape'); await settle(p, 600);
            await ev(c, () => { const el = document.querySelector('.o_form_sheet_bg'); if (el) window.__scroll('.o_form_sheet_bg', 'end', 900); });
            await hold(c, 600); await focus(c, '.oe_subtotal_footer .o_cell_custom@@Маржа'); await hold(c, 1900);
            await title(c, 'Підтвердження', 'Підтвердили — **виробниче замовлення створене само**');
            await press(c, p.locator('button[name="action_confirm"]').first(), { settleMs: 2200 });
            await hold(c, 1800);
        });
    },
    // ---------------------------------------------------------------- виробництво: перетягування картки на дошці = запуск у роботу
    async D_board() {
        return clip('D_board', { role: 'chief', url: '/odoo/action-td_mebli_sale.action_orders_board_td_mebli' }, async (c) => {
            const p = c.page; await settle(p, 1800);
            await ev(c, () => { const s = document.createElement('style'); s.textContent = '.o_kanban_renderer{zoom:.9}'; document.head.appendChild(s); });
            await settle(p, 600); c.mark();
            await title(c, 'Дошка замовлень', 'Беремо замовлення, що чекає, і **перетягуємо у «У виробництві»**', 'Перетягнули картку — **цех стартує**');
            await hold(c, 1300);
            const groups = p.locator('.o_kanban_group');
            const card = groups.nth(2).locator('.o_kanban_record').first();
            await card.waitFor({ state: 'visible' });
            const b = await card.boundingBox();
            const t = await groups.nth(3).boundingBox();
            const x0 = b.x + b.width / 2, y0 = b.y + b.height / 2;
            await glide(c, x0, y0, 600); await sleep(250);
            await p.mouse.down(); await sleep(150);
            const tx = t.x + t.width / 2, ty = Math.min(t.y + 140, 600);
            for (let i = 1; i <= 36; i++) { const k = i / 36, e = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2; await p.mouse.move(x0 + (tx - x0) * e, y0 + (ty - y0) * e - Math.sin(Math.PI * k) * 30); await sleep(28); }
            c.pos = [tx, ty]; await sleep(350); await p.mouse.up(); await settle(p, 1800);
            await title(c, 'Запущено', 'Картка в **«У виробництві»** — перша операція вже стартувала', 'Запущено — **операція вже йде**');
            await hold(c, 2400);
        });
    },
    // ---------------------------------------------------------------- виробництво: дошка, нестача, завантаження (десктоп)
    async D_prod() {
        return clip('D_prod', { role: 'chief', url: '/odoo/action-td_mebli_sale.action_orders_board_td_mebli' }, async (c) => {
            const p = c.page; await settle(p, 1800); c.mark();
            await pain(c, 'Начальник виробництва', 'Статус замовлень — **у чатах і таблицях**, цілісної картини немає');
            await ev(c, () => { const s = document.createElement('style'); s.textContent = '.o_kanban_renderer{zoom:.9}'; document.head.appendChild(s); });
            await title(c, 'Дошка замовлень', 'Усі замовлення за етапами — від пропозиції до готового виробу');
            await scroll(c, '.o_kanban_renderer', 'end', 2200).catch(() => {});
            await ev(c, () => { const k = document.querySelector('.o_kanban_renderer'); if (k) k.scrollLeft = 0; });
            await hold(c, 900);
            await title(c, 'Виробничі замовлення', 'Що **чекає запуску** і чого не вистачає — один список');
            await goto(c, '/odoo/action-mrp.mrp_production_action', 1200);
            await ev(c, () => { const x = document.querySelector('.o_searchview .o_facet_remove'); x && x.click(); });
            await settle(p, 800);
            await press(c, p.locator('.o_searchview_dropdown_toggler'), { settleMs: 500 });
            await press(c, p.locator('.o_search_bar_menu .o_menu_item, .o-dropdown--menu .dropdown-item').filter({ hasText: /Підтверджено/ }).first(), { settleMs: 800 });
            await p.keyboard.press('Escape'); await settle(p, 800);
            await hold(c, 1400);
            await title(c, 'Нестача', 'Нестача фурнітури видна **ще до запуску** — закупівля встигає');
            await press(c, p.locator('.o_data_row').filter({ hasText: /Немає в наявності/ }).first(), { settleMs: 1500 });
            // рядок «Немає в наявності» має бути над плашкою титру: піднімаємо його в верхню частину форми
            await ev(c, () => { const r = [...document.querySelectorAll('tr, .o_data_row')].find((e) => /Немає в наявності/.test(e.innerText)); if (r) r.scrollIntoView({ block: 'start' }); });
            await ev(c, () => { const r = [...document.querySelectorAll('tr, .o_data_row')].find((e) => /Немає в наявності/.test(e.innerText)); if (r) { r.style.outline = '3px solid #FE5000'; r.setAttribute('data-tdhl', '1'); } });
            await focus(c, '[data-tdhl]'); await hold(c, 2400);
            await goto(c, '/odoo/action-td_mebli_mrp.mrp_workorder_td_load_action', 1200);
            await p.waitForSelector('.o_graph_renderer canvas'); await sleep(1500);
            await title(c, 'Завантаження дільниць', 'Де понад 100 % — **вузьке місце видно до зриву**', null, null, true);
            await hold(c, 1500);
            await zoom(c, '.o_graph_renderer', 1.35, 1600); await hold(c, 1900);
        });
    },
    // ---------------------------------------------------------------- технолог: розкрій (десктоп)
    async D_cut() {
        return clip('D_cut', { role: 'tech', url: '/odoo/action-td_mebli_cutting.td_mebli_cutting_job_action' }, async (c) => {
            const p = c.page; await settle(p, 1500); c.mark();
            await pain(c, 'Технолог', 'Відходи плити з’ясовуються **після розкрою**, а обрізки губляться');
            await title(c, 'Розкрій · імітація програми', 'Завдання розкрою: деталі замовлень збираються разом');
            await hold(c, 1200);
            await press(c, p.locator('.o_data_row').filter({ hasText: /CUT\/0026/ }).first(), { settleMs: 1800 });
            await press(c, p.locator('.o_notebook .nav-link').filter({ hasText: /Карта розкрою/ }).first(), { settleMs: 900 });
            await title(c, 'Карта розкрою', 'Відсоток відходів і **обрізки зі складу — першими**');
            await ev(c, () => { const f = document.querySelector('.o_form_sheet_bg'); const nb = f && f.querySelector('.o_notebook'); if (f && nb) window.__scroll('.o_form_sheet_bg', Math.max(0, nb.getBoundingClientRect().top - f.getBoundingClientRect().top + f.scrollTop - 150), 1400); });
            await hold(c, 3500);
        });
    },
    // ---------------------------------------------------------------- комірник: ділові обрізки (десктоп)
    async D_store() {
        return clip('D_store', { role: 'store', url: '/odoo/action-td_mebli_cutting.stock_lot_td_offcut_action' }, async (c) => {
            const p = c.page; await settle(p, 1500); c.mark();
            await pain(c, 'Комірник', 'Залишки й обрізки лежать **поза обліком**, закупівля не бачить потреби');
            await title(c, 'Ділові обрізки', 'Обрізки на обліку: **розмір, площа, резерв** під завдання');
            const heads = p.locator('.o_group_header');
            for (const i of [0, 1]) { if (await heads.nth(i).count()) await press(c, heads.nth(i), { settleMs: 700 }); }
            await ev(c, () => window.__scroll('.o_content', 'end', 2500));
            await hold(c, 1500);
        });
    },
    // ---------------------------------------------------------------- фінансист: маржа замовлень (десктоп)
    async D_margin() {
        return clip('D_margin', { role: 'fin', url: '/odoo/action-td_mebli_sale.sale_order_line_td_cost_action' }, async (c) => {
            const p = c.page; await settle(p, 2000); c.mark();
            await pain(c, 'Фінансист', 'Маржу замовлення з’ясовують, **коли шафа вже виготовлена**');
            await title(c, 'Звіт собівартості', 'Виручка, собівартість і **маржа по замовленнях**');
            await hold(c, 2400);
            await press(c, p.locator('button.o_switch_view.o_list'), { settleMs: 1500 });
            await title(c, 'Низька маржа', 'Замовлення нижче 15 % — **червоним**, одразу видно');
            await ev(c, () => window.__scroll('.o_content', 'end', 2600));
            await focus(c, '.o_data_row:has(.text-danger)'); await hold(c, 2200);
        });
    },
    // ---------------------------------------------------------------- ТЕЛЕФОН: салон — нове замовлення з конфігуратором
    async M_sale() {
        return clip('M_sale', { role: 'salon', mobile: true, url: '/odoo/action-sale.action_quotations' }, async (c) => {
            const p = c.page; await settle(p, 1800);
            await press(c, p.locator('.o-kanban-button-new, .o_list_button_add').first(), { settleMs: 700 });
            await choose(c, p.locator('.o_field_widget[name=partner_id] input'), 'Гончар', 'Гончар');
            await press(c, p.locator('.o_form_button_save'), { settleMs: 1000 });
            await settle(p, 600); c.mark();
            await title(c, 'Менеджер салону', 'Нове замовлення — **просто з телефона**', 'Замовлення — **з телефона**');
            await hold(c, 900);
            await title(c, 'Виріб', 'Додаємо шафу-купе', 'Додаємо **шафу-купе**');
            await press(c, p.getByText('Додати товар').first(), { settleMs: 700 });
            await press(c, p.locator('.modal [name=product_template_id] input').first(), { settleMs: 600 });
            await press(c, p.locator('.modal .o_kanban_record').filter({ hasText: /Шафа-купе/ }).first(), { settleMs: 1100 });
            await p.waitForSelector('.o_sale_product_configurator_dialog'); await settle(p, 700);
            const dlg = p.locator('.o_sale_product_configurator_dialog');
            const ptal = (label) => dlg.locator('div[name="ptal"]').filter({ has: p.locator('label', { hasText: label }) });
            await title(c, 'Конфігуратор', 'Декор, кромка, фурнітура — **ціна одразу**', 'Обираємо **декор** — ціна змінюється');
            await press(c, ptal('Декор корпусу').locator('span', { hasText: 'Антрацит' }).first(), { settleMs: 350 });
            await press(c, ptal('Кромка').locator('span', { hasText: 'ПВХ 2 мм' }).first(), { settleMs: 350 });
            await press(c, ptal('Фурнітура').locator('span', { hasText: 'Преміум' }).first(), { settleMs: 350 });
            await focus(c, '.o_sale_product_configurator_dialog .modal-footer');
            await title(c, 'Розміри', 'Вводимо **розміри покупця**', 'Вводимо **розміри**');
            for (const [label, value] of [['Ширина', '2000'], ['Висота', '2400'], ['Глибина', '600']]) {
                await typeIn(c, ptal(label).locator('input[type="text"]'), value, 70);
                await press(c, dlg.locator('.modal-body'), { settleMs: 250 });
            }
            await focus(c, '.o_sale_product_configurator_dialog .modal-footer'); await hold(c, 600);
            await press(c, dlg.locator('button', { hasText: /Підтвердити|Confirm/ }), { settleMs: 800 });
            await title(c, 'Ціна', 'Ціна за розмірами: **26 400 → 33 000 ₴**', null, { n: '33 000 ₴', l: 'ціна після розмірів покупця (було 26 400)' });
            await focus(c, '.o_data_row, [name="order_line"]'); await hold(c, 1300);
            await press(c, p.locator('.modal button').filter({ hasText: /^\s*Зберегти та закрити\s*$|Save & Close/ }).first(), { settleMs: 600 });
            await hideChatter(c);
            await press(c, p.locator('.o_form_button_save'), { settleMs: 800 });
            await p.waitForFunction(() => !/\(100\s?%\)/.test(document.body.innerText), null, { timeout: 10000 }).catch(() => console.error('WARN M_sale: маржа не перерахована'));
            await title(c, 'Маржа', 'Ціна й **маржа — ще в пропозиції**', null, { n: '34,4 %', l: 'маржа замовлення — видно до підтвердження' });
            await scrollTo(c, '.oe_subtotal_footer .o_cell_custom@@Маржа', 1300, 0.45); await focus(c, '.oe_subtotal_footer .o_cell_custom@@Маржа'); await hold(c, 1300);
            await title(c, 'Підтвердження', 'Підтвердили — **цех уже знає**');
            await scrollAny(c, 0, 800);
            await press(c, p.locator('.o_statusbar_buttons .dropdown-toggle, .o_statusbar_buttons button.o_dropdown_button, button[name="action_confirm"]').first(), { settleMs: 700 });
            const ok = p.locator('.o-dropdown--menu button[name="action_confirm"], .o-dropdown--menu .dropdown-item[name="action_confirm"]');
            if (await ok.count()) await press(c, ok.first(), { settleMs: 1100 });
            await hold(c, 1000);
        });
    },
    // ---------------------------------------------------------------- ТЕЛЕФОН: начальник виробництва — дошка й завантаження
    async M_prod() {
        return clip('M_prod', { role: 'chief', mobile: true, url: '/odoo/action-td_mebli_sale.action_orders_board_td_mebli' }, async (c) => {
            const p = c.page; await settle(p, 2000); c.mark();
            await title(c, 'Начальник виробництва', 'Усі замовлення — **за етапами**');
            await scrollN(c, '.o_kanban_group', 0, 'scrollTop', 520, 1300);
            await scrollN(c, '.o_kanban_renderer', 0, 'scrollLeft', 351, 900);
            await title(c, 'Запуск', 'Що **чекає запуску**, що вже в роботі', null, { n: '13', l: 'замовлень чекають запуску' });
            await scrollN(c, '.o_kanban_group', 1, 'scrollTop', 420, 1200);
            await scrollN(c, '.o_kanban_renderer', 0, 'scrollLeft', 702, 900);
            await scrollN(c, '.o_kanban_group', 2, 'scrollTop', 600, 1100);
            await goto(c, '/odoo/action-td_mebli_mrp.mrp_workorder_td_load_action', 1200);
            await title(c, 'Дільниці', '**Понад 100 %** — вузьке місце', null, { n: '129 %', l: 'Складання — вузьке місце видно до зриву' });
            await p.waitForSelector('.o_graph_renderer canvas'); await sleep(1600);
            await focus(c, '.o_graph_renderer canvas'); await hold(c, 700);
            await press(c, p.locator('.o_graph_renderer canvas'), { settleMs: 600 }); await hold(c, 1300);
        });
    },
    // ---------------------------------------------------------------- ТЕЛЕФОН: комірник — ділові обрізки
    async M_store() {
        return clip('M_store', { role: 'store', mobile: true, url: '/odoo/action-td_mebli_cutting.stock_lot_td_offcut_action' }, async (c) => {
            const p = c.page; await settle(p, 2000);
            await ev(c, () => { document.querySelectorAll('.o_searchview .o_facet_remove').forEach((x) => x.click()); });
            await settle(p, 1000); c.mark();
            await title(c, 'Комірник', 'Ділові обрізки: **розмір, площа, резерв**');
            await hold(c, 700); await scrollN(c, '.o_kanban_group', 0, 'scrollTop', 520, 1700);
            await title(c, 'Резерв', 'Наступний розкрій **бере їх першими**');
            await scrollTo(c, '^.o_kanban_record:has(.text-bg-warning)', 1500, 0.3); await focus(c, '^.o_kanban_record:has(.text-bg-warning)'); await hold(c, 1100);
            await scrollTo(c, '.o_kanban_record:has(.text-bg-warning)', 1300, 0.3); await hold(c, 500);
        });
    },
    // ---------------------------------------------------------------- ТЕЛЕФОН: власник/фінансист — маржа замовлень
    async M_margin() {
        return clip('M_margin', { role: 'owner', mobile: true, url: '/odoo/action-td_mebli_sale.sale_order_line_td_cost_action' }, async (c) => {
            const p = c.page; await settle(p, 2000);
            await ev(c, () => { const b = document.querySelector('button.o_switch_view.o_kanban'); b && b.click(); });
            await settle(p, 1500); c.mark();
            await title(c, 'Власник · фінансист', 'Маржа кожного замовлення — **на екрані**');
            await hold(c, 1400);
            await scrollAny(c, 600, 2000);
            await title(c, 'Низька маржа', 'Нижче 15 % — **червоним**');
            await scrollTo(c, '^.o_kanban_record:has(.o_field_percentage.text-danger)', 1500, 0.3); await focus(c, '^.o_kanban_record:has(.o_field_percentage.text-danger)'); await hold(c, 1200);
            await scrollTo(c, '.o_kanban_record:has(.o_field_percentage.text-danger)', 1100, 0.3); await hold(c, 500);
        });
    },
};

const names = process.argv.slice(2);
await launch();
for (const n of names) { if (!CLIPS[n]) { console.error('немає кліпа', n); continue; } await CLIPS[n](); }
process.exit(0);
