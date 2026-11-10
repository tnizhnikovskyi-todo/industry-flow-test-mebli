// Сценарій показу пакета «меблі» в справжньому Odoo 19 (PLAN.md §6, SHOW.md): продаючі скриншоти й відео.
// Запуск: node scenario.mjs [порт]   Env: BASE, DB (mebli_demo), ONLY=1,2,3 (зняти лише ці кроки; потрібна база після кроків 1-5).
// Усі дії - справжні кліки в інтерфейсі Odoo (не RPC). Користувачі й дані - з td_mebli_demo/showcase.py.
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const __dirname = path.dirname(fileURLToPath(import.meta.url));

const ROOT = path.resolve(__dirname, '..');
const BASE = process.env.BASE || `http://127.0.0.1:${process.argv[2] || 19071}`;
const DB = process.env.DB || 'mebli_demo';
const SHOTS = path.join(ROOT, 'screens');
const VIDEO = path.join(ROOT, 'video');
const IMG = path.resolve(ROOT, '../../../../package/addons/td_mebli_demo/static/img');
const DOMAIN = 'demo-fabryka.example';
fs.mkdirSync(SHOTS, { recursive: true });
fs.mkdirSync(VIDEO, { recursive: true });

const ROLES = {
    salon: { name: 'Олена Мартинюк', role: 'Менеджер салону' },
    tech: { name: 'Андрій Ковальчук', role: 'Технолог-конструктор' },
    chief: { name: 'Ігор Савчук', role: 'Начальник виробництва' },
    store: { name: 'Марія Гнатюк', role: 'Комірник' },
    fin: { name: 'Наталія Бондар', role: 'Фінансист' },
    owner: { name: 'Віталій Остапенко', role: 'Власник · директор фабрики' },
};
for (const [k, r] of Object.entries(ROLES)) {
    r.avatar = 'data:image/png;base64,' + fs.readFileSync(path.join(IMG, `avatar_${k}.png`)).toString('base64');
}
const b64 = (f) => fs.readFileSync(path.join(ROOT, 'brand-todo', f)).toString('base64');
const FONT_CSS = `@font-face{font-family:'Open Sans';font-weight:400;src:url(data:font/ttf;base64,${b64('fonts/OpenSans-regular.ttf')})}@font-face{font-family:'Open Sans';font-weight:700;src:url(data:font/ttf;base64,${b64('fonts/OpenSans-bold.ttf')})}`;
const TODO_MARK = 'data:image/png;base64,' + b64('todo-mark.png');
const LOGO = 'data:image/png;base64,' + fs.readFileSync(path.join(IMG, 'logo.png')).toString('base64');

let page, context;
let n = 0;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const ONLY = process.env.ONLY ? process.env.ONLY.split(',').map(Number) : null;
const READ = parseFloat(process.env.READ || '0.05'); // множник часу читання підписів

// ---------------------------------------------------------------- підписи на екрані (для відео й скриншотів)
const OVERLAY_JS = () => `(() => {
  if (window.__capInstalled) return; window.__capInstalled = true;
  const css = document.createElement('style');
  css.textContent = ${JSON.stringify(FONT_CSS)} + \`
    .o_web_client, .o_action_manager { max-height: calc(100vh - 104px); }
    .o_web_client { height: calc(100vh - 104px) !important; }
    #td-cap { position: fixed; left: 0; right: 0; bottom: 0; height: 104px; z-index: 100000; display: flex; align-items: center; gap: 18px;
      padding: 0 28px; background: #101820; color: #fff; font-family: "Open Sans", sans-serif; box-sizing: border-box; border-top: 6px solid #FE5000; }
    #td-cap img { width: 56px; height: 56px; border-radius: 50%; border: 2px solid #FE5000; flex: none; } #td-cap img.mark { width: 40px; height: 40px; border-radius: 8px; border: 0; background: #fff; padding: 3px; }
    #td-cap .who { width: 190px; flex: none; line-height: 1.25; }
    #td-cap .who b { display: block; font-size: 16px; } #td-cap .who span { font-size: 13px; color: #BFBFBF; }
    #td-cap .txt { flex: 1; line-height: 1.3; }
    #td-cap .pain { font-size: 13.5px; color: #BFBFBF; margin-bottom: 3px; }
    #td-cap .gain { font-size: 20px; font-weight: 600; }
    #td-cap .tags { flex: none; display: flex; flex-direction: column; gap: 6px; align-items: flex-end; }
    #td-cap .tag.dim { color: #BFBFBF; border-color: #808080; font-size: 10.5px; }
    #td-cap .tag { flex: none; font-size: 11.5px; letter-spacing: .04em; text-transform: uppercase; color: #FE5000; border: 1px solid #FE5000;
      border-radius: 20px; padding: 3px 11px; white-space: nowrap; }
    #td-card { position: fixed; inset: 0; z-index: 200000; background: #2b2118; color: #fff; display: flex; flex-direction: column; align-items: center;
      justify-content: center; text-align: center; font-family: "Inter", "Segoe UI", Roboto, sans-serif; padding: 0 120px; }
    #td-card img.logo { width: 120px; height: 120px; border-radius: 26px; margin-bottom: 28px; }
    #td-card h1 { font-size: 46px; margin: 0 0 14px; font-weight: 700; } #td-card h2 { font-size: 24px; margin: 0 0 30px; font-weight: 400; color: #e8d6bb; }
    #td-card .crew { display: flex; gap: 26px; margin-top: 8px; } #td-card .crew div { width: 150px; font-size: 14px; color: #e8d6bb; line-height: 1.3; }
    #td-card .crew img { width: 84px; height: 84px; border-radius: 50%; border: 3px solid #c9a06a; display: block; margin: 0 auto 8px; }
    #td-card ul { text-align: left; font-size: 24px; line-height: 1.7; margin: 0; padding-left: 26px; } #td-card .note { margin-top: 34px; font-size: 14px; color: #bfa780; }
  \`;
  const mount = () => {
    if (!document.head || !document.body) return;
    document.head.appendChild(css);
    const el = document.createElement('div'); el.id = 'td-cap'; el.style.display = 'none'; document.body.appendChild(el);
    window.__renderCap = () => {
      let c = null; try { c = JSON.parse(sessionStorage.getItem('td_cap') || 'null'); } catch (e) {}
      el.style.display = c ? 'flex' : 'none'; document.body.classList.toggle('td-has-cap', !!c);
      if (!c) { css.disabled = true; return; } css.disabled = false;
      el.innerHTML = '<img src="' + c.avatar + '"><div class="who"><b>' + c.name + '</b><span>' + c.role + '</span></div>' +
        '<div class="txt"><div class="pain">Біль: ' + c.pain + '</div><div class="gain">' + c.gain + '</div></div>' +
        '<div class="tags"><span class="tag dim">' + (c.tag || 'демо-дані') + '</span></div><img class="mark" src="${TODO_MARK}">';
    };
    window.__renderCap();
  };
  if (document.body) mount(); else document.addEventListener('DOMContentLoaded', mount);
})();`;

async function caption(roleKey, pid, pain, gain, tag) {
    const r = ROLES[roleKey];
    const cap = { ...r, pid, pain, gain, tag };
    await page.evaluate((c) => { sessionStorage.setItem('td_cap', JSON.stringify(c)); window.__renderCap && window.__renderCap(); }, cap);
}
const CARD_CSS = `<style>
  html, body { margin: 0; height: 100%; background: #2b2118; }
  body { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; color: #fff;
    font-family: "Inter", "Segoe UI", Roboto, "Helvetica Neue", sans-serif; padding: 0 120px; box-sizing: border-box; }
  img.logo { width: 140px; height: 140px; border-radius: 30px; margin-bottom: 30px; }
  h1 { font-size: 46px; margin: 0 0 14px; font-weight: 700; line-height: 1.2; } h2 { font-size: 24px; margin: 0 0 30px; font-weight: 400; color: #e8d6bb; }
  .crew { display: flex; gap: 26px; margin-top: 8px; } .crew div { width: 150px; font-size: 14px; color: #e8d6bb; line-height: 1.3; }
  .crew img { width: 84px; height: 84px; border-radius: 50%; border: 3px solid #c9a06a; display: block; margin: 0 auto 8px; }
  ul { text-align: left; font-size: 24px; line-height: 1.7; margin: 0; padding-left: 26px; } .note { margin-top: 34px; font-size: 14px; color: #bfa780; }
  .who img { width: 150px; height: 150px; border-radius: 50%; border: 4px solid #c9a06a; margin-bottom: 22px; } .who .k { font-size: 15px; letter-spacing: .08em; text-transform: uppercase; color: #bfa780; margin-bottom: 8px; }
</style>`;
// a full-screen standalone page (not injected into Odoo): the video starts and ends on these
async function card(html, ms) {
    // setContent over a live Odoo page left its owl code running on a destroyed DOM (pageerror «parentNode of null»): leave the page first
    await page.goto('about:blank');
    await page.setContent('<!doctype html><html lang="uk"><head><meta charset="utf-8">' + CARD_CSS + '</head><body>' + html + '</body></html>');
    await sleep(ms * READ);
}
async function roleCard(roleKey, line) {
    const r = ROLES[roleKey];
    await card(`<div class="who"><div class="k">${line}</div><img src="${r.avatar}"><h1>${r.name}</h1><h2>${r.role}</h2></div>`, 2600);
}
// pre-login of every role outside the recording: the video never shows the Odoo login page
const COOKIES = {};
async function prelogin(browser) {
    for (const key of Object.keys(ROLES)) {
        const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
        const pg = await ctx.newPage();
        await pg.goto(`${BASE}/web/login?db=${DB}`);
        await pg.fill('input[name=login]', `${key}@${DOMAIN}`);
        await pg.fill('input[name=password]', 'demo');
        await pg.click('button[type=submit]');
        await pg.waitForSelector('.o_navbar', { timeout: 30000 });
        COOKIES[key] = await ctx.cookies();
        await ctx.close();
    }
}
async function asRole(roleKey, line, url) {
    await roleCard(roleKey, line);
    await context.clearCookies();
    await context.addCookies(COOKIES[roleKey]);
    await page.goto(BASE + url);
    await settle(1800);
    await page.evaluate(() => { sessionStorage.removeItem('td_cap'); window.__renderCap && window.__renderCap(); });
}
async function compact(on) {
    await page.evaluate((flag) => {
        let el = document.getElementById('td-compact');
        if (!el) { el = document.createElement('style'); el.id = 'td-compact'; document.head.appendChild(el); }
        el.textContent = flag ? '.o_list_renderer td, .o_list_renderer th { padding-top: 3px !important; padding-bottom: 3px !important; } .o_list_renderer .o_data_row { height: 30px; }' : '';
    }, on);
}

// ---------------------------------------------------------------- допоміжні дії
async function settle(ms = 700) {
    await page.waitForLoadState('load').catch(() => {});
    await page.waitForFunction(() => !document.querySelector('.o_loading, .o_blockUI, .o_ui_blocked'), null, { timeout: 8000 }).catch(() => {});
    await sleep(ms);
}
async function goto(url) { await page.goto(BASE + url); await settle(1200); }
async function shot(name, hold = 6500) {
    n += 1;
    // таблиця деталей широка: на цих кадрах ховаємо чат справа, щоб колонки не різались
    await page.evaluate((on) => { let el = document.getElementById('td-nochat'); if (!el) { el = document.createElement('style'); el.id = 'td-nochat'; document.head.appendChild(el); }
        el.textContent = on ? '.o-mail-Form-chatter, .o-mail-ChatterContainer { display: none !important; }' : ''; }, ['specyfikaciya', 'zavdannya-rozkroyu'].includes(name));
    await page.mouse.move(880, 960); // курсор у підписі: жодних підказок і підсвічування в кадрі
    await settle(600);
    const file = path.join(SHOTS, `${String(n).padStart(2, '0')}-${name}.png`);
    await page.screenshot({ path: file });
    console.log('shot', path.basename(file));
    await sleep(hold * READ); // час прочитати підпис у відео
}
async function clickText(selector, re, opts = {}) {
    const loc = page.locator(selector).filter({ hasText: re }).first();
    await loc.waitFor({ state: 'visible', timeout: 15000 });
    await loc.click(opts);
    await settle();
}
async function menu(sectionXmlid, itemXmlid) {
    if (sectionXmlid) {
        await page.locator(`.o_menu_sections [data-menu-xmlid="${sectionXmlid}"]`).first().click();
        await sleep(300);
    }
    await page.locator(`[data-menu-xmlid="${itemXmlid}"]`).first().click();
    await settle(1200);
}
async function openApp(xmlid) {
    await page.locator('.o_navbar_apps_menu button, .o_menu_toggle').first().click();
    await sleep(300);
    await page.locator(`.o-dropdown--menu [data-menu-xmlid="${xmlid}"], .o_app[data-menu-xmlid="${xmlid}"]`).first().click();
    await settle();
}
const notebookTab = (re) => clickText('.o_notebook .nav-link', re);
async function removeFacet() {
    const x = page.locator('.o_searchview .o_facet_remove').first();
    if (await x.count()) { await x.click(); await settle(800); }
}
const want = (i) => !ONLY || ONLY.includes(i);
// ---- факти для SHOW.md: беруться з тієї самої бази й тих самих кадрів, що й зйомка (shoot/facts.json -> make_show.mjs)
const facts = { checks: [] };
async function rpc(model, method, args, kwargs = {}) {
    return page.evaluate(async ([model, method, args, kwargs]) => {
        const r = await fetch(`/web/dataset/call_kw/${model}/${method}`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: { model, method, args, kwargs } }) });
        const j = await r.json(); if (j.error) throw new Error((j.error.data && j.error.data.message) || 'rpc error'); return j.result;
    }, [model, method, args, kwargs]);
}
const norm = (t) => String(t).replace(/[\u00a0\u202f]/g, ' ').trim();
const pageText = async () => norm(await page.evaluate(() => document.body.innerText));
async function check(name, expected) { // число з SHOW.md має бути в DOM кадру
    const ok = (await pageText()).includes(expected);
    facts.checks.push({ name, expected, ok });
    if (!ok) console.error('FACT MISMATCH', name, expected);
}
let step = 0;
const next = () => { step += 1; return step; };

// ---------------------------------------------------------------- сценарій
let orderId = null;
async function steps() {
    await card(`<img class="logo" src="${LOGO}"><h1>Меблева фабрика «Демо»</h1>
      <h2>Від замовлення покупця до готового виробу — в одній системі</h2>
      <div class="crew">${['salon', 'tech', 'chief', 'store', 'fin'].map((k) => `<div><img src="${ROLES[k].avatar}">${ROLES[k].name}<br>${ROLES[k].role}</div>`).join('')}</div>
      <div class="note">Показ на вигаданих даних · Odoo 19 + модулі пакета «меблі»</div>`, 6000);

    // ===== Менеджер салону =====
    await asRole('salon', 'Крок 1 · Салон: прийняти замовлення', '/odoo/action-sale.product_template_action');
    let s;
    if (want((s = next()))) { // 1 каталог: виріб і його опції
        await goto('/odoo/action-sale.product_template_action');
        const search = page.locator('.o_searchview_input');
        await search.fill('Шафа-купе'); await search.press('Enter'); await settle(1200);
        await page.locator('.o_kanban_record, .o_data_row').filter({ hasText: /Шафа-купе/ }).first().click();
        await settle(1500);
        await notebookTab(/Атрибути|Attributes/);
        await caption('salon', 'PAIN-02', 'опції виробу (декор, кромка, фурнітура, розмір) рахують на калькуляторі',
            'Усі опції виробу вже в картці, кожна з доплатою. Менеджеру не потрібен калькулятор.');
        await shot('katalog-vyrib');
    }
    if (want((s = next()))) { // 2 конфігуратор
        await goto('/odoo/action-sale.action_quotations');
        await page.locator('.o_list_button_add, .o-kanban-button-new').first().click();
        await settle();
        await page.locator('.o_field_widget[name=partner_id] input').fill('Шевчук');
        await page.locator('ul.ui-autocomplete > li > a').first().click();
        await settle();
        await page.locator('.o_form_button_save').click(); // замовлення отримує номер ще до вибору виробу
        await settle(1500);
        await page.locator('a:has-text("Додати товар"), a:has-text("Add a product")').first().click();
        await page.locator('div[name="product_template_id"] input').fill('Шафа-купе');
        await page.locator('ul.ui-autocomplete > li > a').filter({ hasText: /Шафа-купе/ }).first().click();
        await page.waitForSelector('.o_sale_product_configurator_dialog');
        await settle();
        const dlg = page.locator('.o_sale_product_configurator_dialog');
        const ptal = (label) => dlg.locator('div[name="ptal"]').filter({ has: page.locator('label', { hasText: label }) });
        await ptal('Декор корпусу').locator('span', { hasText: 'Дуб Сонома' }).first().click();
        await ptal('Декор фасаду').locator('span', { hasText: 'Антрацит' }).first().click();
        await ptal('Кромка').locator('span', { hasText: 'ПВХ 2 мм' }).first().click();
        await ptal('Фурнітура').locator('span', { hasText: 'Преміум' }).first().click();
        for (const [label, value] of [['Ширина', '1800'], ['Висота', '2400'], ['Глибина', '600']]) {
            const inp = ptal(label).locator('input[type="text"]');
            await inp.fill(value);
            await dlg.locator('.modal-body').click({ position: { x: 5, y: 5 } });
            await settle(300);
        }
        await caption('salon', 'PAIN-02', 'покупець змінює декор чи фурнітуру — і ціну рахують заново',
            'Покупець обирає декор, кромку й фурнітуру, називає розміри — менеджер збирає виріб прямо при ньому.');
        await shot('konfigurator');
        await dlg.locator('button', { hasText: /Підтвердити|Confirm/ }).click();
        await page.waitForSelector('.o_sale_product_configurator_dialog', { state: 'detached' });
        await settle(1000);
        await page.locator('.o_form_button_save').click();
        await settle(1500);
        orderId = (/(\d+)$/.exec(page.url()) || [])[1];
    }
    if (want((s = next()))) { // 3 «а якщо трохи ширше?» і специфікація
        await page.locator('.o_data_row [name="product_template_id"]').first().click();
        await sleep(800);
        await page.locator('.o_data_row button.fa-pencil').first().click(); // «а якщо трохи ширше?» — той самий конфігуратор
        await page.waitForSelector('.o_sale_product_configurator_dialog');
        await settle(800);
        const dlg3 = page.locator('.o_sale_product_configurator_dialog');
        const width = dlg3.locator('div[name="ptal"]').filter({ has: page.locator('label', { hasText: 'Ширина' }) }).locator('input[type="text"]');
        await width.fill('2000');
        await dlg3.locator('.modal-body').click({ position: { x: 5, y: 5 } });
        await sleep(1200);
        await dlg3.locator('button', { hasText: /Підтвердити|Confirm/ }).click();
        await page.waitForSelector('.o_sale_product_configurator_dialog', { state: 'detached' });
        await settle(1200);
        await page.locator('.o_form_button_save').click().catch(() => {});
        await settle(1500);
        await page.locator('.o_data_row button:has(.fa-cogs)').click();
        await settle(1800);
        await notebookTab(/Деталі/);
        await caption('salon', 'PAIN-03', 'специфікацію вручну переносять між програмами проєктування, розкрою й обліку',
            'Покупець попросив ширше — ціна перерахована, а специфікація (плити, кромка, деталі з розмірами) складена сама.');
        await shot('specyfikaciya');
    }
    if (want((s = next()))) { // 4 ціна і маржа
        await page.locator('.breadcrumb-item:not(.active)').last().click();
        await settle(1500);
        await page.locator('.o_optional_columns_dropdown_toggle').first().click();
        await sleep(400);
        const toggle = async (re, on) => {
            const box = page.locator('.o-dropdown--menu .dropdown-item').filter({ hasText: re }).first().locator('input[type=checkbox]');
            if ((await box.count()) && (await box.isChecked()) !== on) await box.click();
        };
        await toggle(/^\s*Розмірний коефіцієнт/, false);
        await toggle(/^\s*Одиниці/, false);
        await toggle(/^\s*Маржа\s*$/, true);
        await page.keyboard.press('Escape');
        await settle(800);
        await page.locator('.o_form_sheet_bg').first().evaluate((el) => { el.scrollTop = el.scrollHeight; });
        await sleep(500);
        await caption('salon', 'PAIN-11', 'маржу замовлення з’ясовують, коли шафа вже виготовлена',
            'Ціна з розмірами й маржа — видно ще в пропозиції, до підтвердження.');
        await check('маржа у пропозиції', '39,13');
        await shot('cina-i-marzha');
    }
    if (want((s = next()))) { // 5 комерційна пропозиція з логотипом
        await goto(`/report/html/sale.report_saleorder/${orderId}`);
        await page.evaluate(() => { document.body.style.background = '#e9e4dc'; document.body.style.zoom = '0.82'; window.scrollTo(0, 0); });
        await caption('salon', 'PAIN-02', 'пропозицію покупцю оформлюють вручну, у кожного менеджера — по-своєму',
            'Комерційна пропозиція з логотипом і реквізитами фабрики — готова з тих самих даних.');
        await shot('komerciyna-propoziciya');
    }
    if (want((s = next()))) { // 6 підтвердження
        await goto(`/odoo/action-sale.action_quotations/${orderId}`);
        await page.locator('button[name="action_confirm"]').first().click();
        await settle(2500);
        await caption('salon', 'PAIN-05', 'виробництво дізнається про замовлення по телефону й зі слів',
            'Підтвердили — виробниче замовлення створене само, його номер видно прямо в замовленні.');
        await shot('pidtverdzhennya');
    }

    // ===== Начальник виробництва =====
    await asRole('chief', 'Крок 2 · Виробництво: що в роботі', '/odoo/action-td_mebli_sale.action_orders_board_td_mebli');
    if (want((s = next()))) { // 7 дошка замовлень
        await goto('/odoo/action-td_mebli_sale.action_orders_board_td_mebli');
        await sleep(800);
        await page.addStyleTag({ content: '.o_kanban_renderer { zoom: 0.86; }' });
        await sleep(500);
        await caption('chief', 'PAIN-05', 'статус замовлення — у чатах і таблицях, цілісної картини немає',
            'Усі замовлення за етапами — від пропозиції до готового виробу, з маржею і часом очікування запуску.');
        await shot('doshka-zamovlen');
    }
    if (want((s = next()))) { // 8 список МО
        await goto('/odoo/action-mrp.mrp_production_action');
        await removeFacet();
        await compact(true);
        await caption('chief', 'PAIN-05', 'незрозуміло, які замовлення чекають на розкрій, а які вже в роботі',
            'Усі виробничі замовлення в одному списку: клієнт, термін, що в роботі, чого не вистачає. Червоним — те, що за планом не встигає в термін.');
        await shot('spysok-vyrobnytstva');
    }
    if (want((s = next()))) { // 9 форма МО із нестачею
        await compact(false);
        await page.locator('.o_data_row').filter({ hasText: /Немає в наявності/ }).first().click();
        await settle(1800);
        await page.locator('.o_form_sheet_bg').first().evaluate((el) => { el.scrollTop = 70; });
        await caption('chief', 'PAIN-07', 'про нестачу фурнітури дізнаються на складанні, коли шафа майже готова',
            'Нестача розсувної системи видна ще до запуску — закупівля встигає її замовити.');
        await shot('mo-nestacha');
    }
    if (want((s = next()))) { // 10 завантаження дільниць
        await goto('/odoo/action-td_mebli_mrp.mrp_workorder_td_load_action');
        const loads = await rpc('mrp.workorder', 'formatted_read_group', [[['state', 'not in', ['done', 'cancel']]], ['workcenter_id'], ['td_load_pct:sum']]);
        facts.loads = loads.map((g) => ({ name: g.workcenter_id[1], pct: Math.round(g['td_load_pct:sum']) })).sort((a, b) => a.pct - b.pct);
        await caption('chief', 'PAIN-06', 'не вистачає людей або зникло світло — план летить, а де саме, не видно',
            'Завантаження кожної дільниці у % від потужності: де понад 100% — там вузьке місце, і видно його до зриву термінів.');
        await shot('zavantazhennya-dilnyc');
    }

    // ===== Технолог-конструктор =====
    await asRole('tech', 'Крок 3 · Розкрій плит', '/odoo/action-mrp.mrp_production_action');
    if (want((s = next()))) { // 11 завдання розкрою
        await goto('/odoo/action-mrp.mrp_production_action');
        await removeFacet();
        await page.locator('.o_searchview_dropdown_toggler').click();
        await clickText('.o_search_bar_menu .o_menu_item, .o-dropdown--menu .dropdown-item', /Підтверджено/);
        await page.keyboard.press('Escape');
        await settle(1000);
        await page.locator('.o_list_renderer thead .o_list_record_selector input').click();
        await page.locator('.o_cp_action_menus button').filter({ hasText: /Дії/ }).click();
        await clickText('.o-dropdown--menu .o_menu_item, .o-dropdown--menu .dropdown-item', /Створити завдання розкрою/);
        await settle(2000);
        await clickText('.o_statusbar_buttons button', /Передати на розкрій/);
        await settle(1500);
        await caption('tech', 'PAIN-04', 'розкрій під кожне замовлення — щоразу окрема ручна задача',
            'Деталі всіх замовлень дня збираються в одне завдання й передаються на розкрій.',
            'Розкрій — імітація програми');
        await shot('zavdannya-rozkroyu');
    }
    if (want((s = next()))) { // 12 результат і карта
        await clickText('.o_statusbar_buttons button', /Отримати результат/);
        await settle(2500);
        await notebookTab(/Карта розкрою/).catch(() => {});
        await page.locator('.o_form_sheet_bg').first().evaluate((el) => {
            const nb = el.querySelector('.o_notebook');
            el.scrollTop = Math.max(0, nb.getBoundingClientRect().top - el.getBoundingClientRect().top + el.scrollTop - 285);
        });
        await caption('tech', 'PAIN-04 · 08', 'відходи плити з’ясовуються тільки після розкрою, а обрізки губляться',
            'Карта розкрою з відсотком відходів. Обрізки зі складу беруться першими — економія в гривнях видна одразу.',
            'Розкрій — імітація програми');
        const jobId = +(/(\d+)$/.exec(page.url()) || [])[1];
        const [job] = await rpc('td.mebli.cutting.job', 'read', [[jobId], ['waste_pct', 'offcut_used_m2', 'offcut_saving']]);
        const nf = (x, d) => x.toFixed(d).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
        facts.cut_m2 = nf(job.offcut_used_m2, 2); facts.cut_saving = nf(job.offcut_saving, 2); facts.cut_waste = nf(job.waste_pct, 1);
        await check('розкрій: площа з обрізків', facts.cut_m2); await check('розкрій: економія', facts.cut_saving); await check('розкрій: відходи', facts.cut_waste);
        await shot("karta-rozkroyu", 8000);
        await clickText('.o_statusbar_buttons button', /Підтвердити/);
        await settle(2500);
    }

    // ===== Комірник =====
    await asRole('store', 'Крок 4 · Склад: обрізки', '/odoo/action-td_mebli_cutting.stock_lot_td_offcut_action');
    if (want((s = next()))) { // 13 ділові обрізки
        await goto('/odoo/action-td_mebli_cutting.stock_lot_td_offcut_action');
        const headers = page.locator('.o_group_header');
        for (const i of [2, 1]) { await headers.nth(i).click().catch(() => {}); await sleep(500); }
        await caption('store', 'PAIN-08', 'залишки й обрізки лежать поза обліком, закупівля не бачить потреби',
            'Ділові обрізки — на обліку з розмірами й площею. Наступний розкрій бере їх у першу чергу.');
        await shot('dilovi-obrizky');
    }

    // ===== Начальник виробництва: факт =====
    await asRole('chief', 'Крок 5 · Підсумки по замовленню', '/odoo/action-mrp.mrp_production_action');
    if (want((s = next()))) { // 14 план/факт
        await goto('/odoo/action-mrp.mrp_production_action');
        await removeFacet();
        await page.locator('.o_searchview_dropdown_toggler').click();
        await clickText('.o_search_bar_menu .o_menu_item, .o-dropdown--menu .dropdown-item', /Виконано/);
        await page.keyboard.press('Escape');
        await settle(1000);
        await page.locator('.o_data_row').filter({ hasText: /Кравець/ }).first().click();
        await settle(1500);
        await page.locator('.o-form-buttonbox .oe_stat_button, .o_form_statusbar button').filter({ hasText: /Огляд/ }).first().click();
        await settle(2500);
        const opt = async (re, on) => {
            await page.locator('button:has-text("Відобразити")').first().click();
            await sleep(400);
            const item = page.locator('.o-dropdown--menu .dropdown-item').filter({ hasText: re }).first();
            const isOn = await item.evaluate((el) => el.classList.contains('selected'));
            if (isOn !== on) await item.click();
            await sleep(500);
            await page.keyboard.press('Escape');
            await sleep(300);
        };
        await opt(/Собівартість по специфікації/, true);
        await opt(/Вартості MO/, false);
        await opt(/Вартість одиниці/, false);
        await page.keyboard.press('Escape');
        await settle(1200);
        await page.evaluate(() => { const el = document.createElement('style'); el.textContent = '.o_content table td, .o_content table th { padding-top: 2px !important; padding-bottom: 2px !important; line-height: 1.25; }'; document.head.appendChild(el); });
        await settle(600);
        const top = await page.evaluate(() => { const tr = [...document.querySelectorAll('tbody tr')].find((r) => /₴/.test(r.innerText)); const c = [...tr.querySelectorAll('td')].map((x) => x.innerText); return c.slice(-2); });
        facts.plan_cost = norm(top[0]); facts.real_cost = norm(top[1]);
        await check('plan-fakt plan', facts.plan_cost); await check('plan-fakt real', facts.real_cost);
        await caption('chief', 'PAIN-11', 'фактична собівартість замовлення відома лише заднім числом',
            'План і факт поруч: вартість матеріалів і годин за специфікацією проти реальної — відхилення видно по рядках.');
        await shot('plan-fakt');
    }
    if (want((s = next()))) { // 15 час до запуску
        await goto('/odoo/action-td_mebli_sale.action_orders_launch_td_mebli');
        await compact(true);
        const footRaw = await page.evaluate(() => [...document.querySelectorAll('.o_list_renderer tfoot td')].map((t) => t.innerText.trim()).find((t) => /^\d+,\d{2}$/.test(t)) || '');
        if (!footRaw) console.error('FACT MISMATCH avg launch: немає підсумку у списку');
        facts.avg_launch = footRaw.replace(/,(\d)\d$/, ',$1');
        facts.avg_launch_raw = footRaw;
        await check('avg launch', facts.avg_launch_raw);
        await caption('chief', 'PAIN-05', 'скільки замовлення чекає, перш ніж потрапити у виробництво, ніхто не знає',
            `Годин від замовлення до початку роботи — по кожному замовленню; середнє внизу: ${facts.avg_launch} год.`);
        await shot('chas-do-zapusku');
    }

    // ===== Фінансист =====
    await asRole('fin', 'Крок 6 · Фінанси: маржа', '/odoo/action-td_mebli_sale.sale_order_line_td_cost_action');
    if (want((s = next()))) { // 16 маржа
        await goto('/odoo/action-td_mebli_sale.sale_order_line_td_cost_action');
        await page.locator('button.o_switch_view.o_list').click().catch(() => {});
        await settle(1500);
        await compact(true);
        await caption('fin', 'PAIN-10 · 11', 'ціни матеріалів змінюються, а маржу замовлень бачать лише після відвантаження',
            'Планова собівартість і маржа кожного замовлення — в одному звіті; замовлення з низькою маржею видно відразу.');
        facts.margins = await page.evaluate(() => [...document.querySelectorAll('.o_list_renderer .o_data_row td')].map((t) => t.innerText.trim()).filter((t) => /^-?\d+[,.]\d+\s?%$/.test(t)).map((t) => parseFloat(t.replace(',', '.'))));
        await shot('marzha-zamovlen');
    }

    // ===== Керівник: фабрика на одному екрані (td_mebli_dashboard) =====
    await asRole('owner', 'Крок 7 · Керівник: вся фабрика на одному екрані', '/odoo/action-td_mebli_dashboard.action_dashboard');
    if (want((s = next()))) { // 17 дашборд керівника
        await goto('/odoo/action-td_mebli_dashboard.action_dashboard');
        await page.waitForSelector('.td_dash_grid', { timeout: 20000 });
        await sleep(800);
        facts.dash = await rpc('td.mebli.dashboard', 'get_data', [], { context: { lang: 'uk_UA' } });
        for (const k of ['revenue', 'margin', 'launch', 'cutting', 'plan_fact']) await check('дашборд ' + k, norm(facts.dash.cards[k].value));
        await caption('owner', 'PAIN-10 · 11', 'щоб побачити фабрику, власник просить звіти у п’яти людей і збирає їх сам',
            'Дашборд керівника: виручка, маржа, час до запуску, дільниці, відхід розкрою, план/факт — на одному екрані.');
        await shot('dashboard-kerivnyka', 9000);
    }

    await card(`<img class="logo" src="${LOGO}"><h1>Одна система замість п’яти програм і таблиць</h1>
      <ul><li>Замовлення з опціями, ціною й маржею — ще до підтвердження</li>
      <li>Специфікація й виробниче замовлення — з опцій, без перенесення вручну</li>
      <li>Розкрій, відходи й ділові обрізки — під обліком</li>
      <li>Завантаження дільниць і план проти факту — на екрані</li></ul>
      <div class="note">Розкрій у цьому показі — імітація програми розкрою; є інтерфейс прийому файлу результату; підключення конкретної програми розкрою тут не показано. Усі дані вигадані.</div>`, 8000);
}

(async () => {
    const browser = await chromium.launch();
    await prelogin(browser);
    context = await browser.newContext({
        viewport: { width: 1440, height: 900 }, locale: 'uk-UA', timezoneId: 'Europe/Kyiv',
        deviceScaleFactor: 2,
    });
    await context.addInitScript(OVERLAY_JS());
    page = await context.newPage();
    page.setDefaultTimeout(20000);
    page.on('pageerror', (e) => console.error('PAGEERR step', step, (e.stack || String(e)).replace(/\n/g, ' | ').slice(0, 600)));
    page.on('console', (m) => { if (m.type() === 'error') console.error('CONSOLE step', step, m.text().slice(0, 300)); });
    let failed = null;
    try {
        await steps();
    } catch (e) {
        failed = e;
        await page.screenshot({ path: process.env.FAIL_SHOT || '/tmp/fail.png' }).catch(() => {});
        console.error('FAIL at step', step, e.message.split('\n').slice(0, 6).join('\n'));
    }
    fs.writeFileSync(path.join(__dirname, 'facts.json'), JSON.stringify(facts, null, 1));
    const video = page.video();
    await context.close();
    if (video) fs.renameSync(await video.path(), path.join(VIDEO, ONLY ? 'partial.webm' : 'scenario-raw.webm'));
    await browser.close();
    process.exit(failed ? 1 : 0);
})();
