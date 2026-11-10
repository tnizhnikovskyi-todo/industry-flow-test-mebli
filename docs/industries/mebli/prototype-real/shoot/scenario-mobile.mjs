// Мобільний показ: справжній Odoo 19 у емуляції телефона (Playwright: 390x844, isMobile, hasTouch, DPR 3). Без записів відео — лише скриншоти
// у screens-mobile/ (рамку телефона малює scenes.mjs у CSS). Використання: node scenario-mobile.mjs [порт] ; ONLY=m1,m3 — вибрані кадри.
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
import fs from 'fs'; import path from 'path';
const here = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(here, '../screens-mobile');
const BASE = process.env.BASE || `http://127.0.0.1:${process.argv[2] || 19071}`;
const DB = process.env.DB || 'mebli_demo';
const ONLY = process.env.ONLY ? process.env.ONLY.split(',') : null;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
fs.mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch();
const DEVICE = { viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true, locale: 'uk-UA', timezoneId: 'Europe/Kyiv' };
async function ctxFor(login) {
    const ctx = await browser.newContext(DEVICE);
    const page = await ctx.newPage();
    page.setDefaultTimeout(20000);
    page.on('pageerror', (e) => console.error('PAGEERR', login, (e.stack || String(e)).replace(/\n/g, ' | ').slice(0, 400)));
    page.on('console', (m) => { if (m.type() === 'error') console.error('CONSOLE', login, m.text().slice(0, 250)); });
    await page.goto(`${BASE}/web/login?db=${DB}`);
    await page.fill('input[name=login]', `${login}@demo-fabryka.example`);
    await page.fill('input[name=password]', 'demo');
    await page.click('button[type=submit]');
    await page.waitForSelector('.o_navbar, .o_main_navbar', { timeout: 30000 });
    return { ctx, page };
}
async function settle(page, ms = 1200) {
    await page.waitForLoadState('load').catch(() => {});
    await page.waitForFunction(() => !document.querySelector('.o_loading, .o_blockUI, .o_ui_blocked'), null, { timeout: 8000 }).catch(() => {});
    await sleep(ms);
}
async function rpc(page, model, method, args, kwargs = {}) {
    return page.evaluate(async ([model, method, args, kwargs]) => {
        const r = await fetch(`/web/dataset/call_kw/${model}/${method}`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: { model, method, args, kwargs } }) });
        const j = await r.json(); if (j.error) throw new Error((j.error.data && j.error.data.message) || 'rpc error'); return j.result;
    }, [model, method, args, kwargs]);
}
const want = (k) => !ONLY || ONLY.includes(k);
async function shot(page, name) {
    await settle(page, 800);
    await page.screenshot({ path: path.join(OUT, `${name}.png`) });
    console.log('shot', name);
}
// «висока» версія кадру для відео: той самий мобільний інтерфейс, але вікно вищого за екран телефона — відео прокручує її плавно
async function tall(page, name, height = 1500) {
    await page.setViewportSize({ width: 390, height });
    await settle(page, 1200);
    await page.screenshot({ path: path.join(OUT, `${name}.png`) });
    console.log('shot', name);
    await page.setViewportSize({ width: 390, height: 844 });
    await settle(page, 600);
}
const go = async (page, url) => { await page.goto(BASE + url); await settle(page, 1500); };

const sessions = {};
const as = async (k) => (sessions[k] ||= await ctxFor(k));
let failed = false;
async function run(key, fn) {
    if (!want(key)) return;
    try { await fn(); } catch (e) { failed = true; console.error('FAIL', key, String(e.message).split('\n').slice(0, 4).join(' | ')); }
}

// m1: менеджер салону — відкрите замовлення з параметричним виробом, конфігуратор у рядку, підтвердження
await run('m1', async () => {
    const { page } = await as('salon');
    await go(page, '/odoo/action-sale.action_quotations');
    const drafts = await rpc(page, 'sale.order', 'search_read', [[['state', '=', 'draft'], ['order_line.td_bom_id', '!=', false]]], { fields: ['id'], limit: 1, order: 'id desc' });
    await go(page, `/odoo/action-sale.action_quotations/${drafts[0].id}`);
    await shot(page, 'm1-zamovlennya');
    await tall(page, 'm1t-zamovlennya-tall', 1700);
    await page.locator('[name="order_line"] .o_kanban_record, .o_field_one2many .o_kanban_record, [name="order_line"] .o_data_row').first().click();
    await settle(page, 1500);
    await shot(page, 'm1c-ryadok');
    await tall(page, 'm1ct-ryadok-tall', 1500);
    await page.goBack().catch(() => {});
    await go(page, `/odoo/action-sale.action_quotations/${drafts[0].id}`);
    await page.locator('.o_statusbar_buttons .dropdown-toggle, .o_statusbar_buttons button.o_dropdown_button').first().click();
    await sleep(500);
    await page.locator('.o-dropdown--menu button[name="action_confirm"], .o-dropdown--menu .dropdown-item[name="action_confirm"]').first().click();
    await settle(page, 2500);
    await shot(page, 'm1b-pidtverdzheno');
    await tall(page, 'm1bt-pidtverdzheno-tall', 1500);
});
// m2: начальник виробництва — дошка замовлень і завантаження дільниць
await run('m2', async () => {
    const { page } = await as('chief');
    await go(page, '/odoo/action-td_mebli_sale.action_orders_board_td_mebli');
    await shot(page, 'm2-doshka');
    await tall(page, 'm2t-doshka-tall', 1500);
    await go(page, '/odoo/action-td_mebli_mrp.mrp_workorder_td_load_action');
    await shot(page, 'm2b-zavantazhennya');
    await tall(page, 'm2bt-zavantazhennya-tall', 1300);
});
// m3: комірник — ділові обрізки (картки: розмір, площа, резерв) і резерв під завдання розкрою
await run('m3', async () => {
    const { page } = await as('store');
    await go(page, '/odoo/action-td_mebli_cutting.stock_lot_td_offcut_action');
    const x = page.locator('.o_searchview .o_facet_remove');
    for (let i = (await x.count()) - 1; i >= 0; i--) { await x.nth(i).click().catch(() => {}); await sleep(400); } // без групування: картки одним списком
    await shot(page, 'm3-obrizky');
    await tall(page, 'm3t-obrizky-tall', 1500);
    const reserved = await rpc(page, 'stock.lot', 'search_read', [[['td_is_offcut', '=', true], ['product_qty', '>', 0]]], { fields: ['name', 'td_reserved_m2'], limit: 200 });
    const hit = reserved.find((l) => l.td_reserved_m2 > 0);
    if (!hit) console.error('FAIL m3b: немає резервованих обрізків');
    else {
        await go(page, '/odoo/action-td_mebli_cutting.stock_lot_td_offcut_action');
        const rm = page.locator('.o_searchview .o_facet_remove');
        for (let i = (await rm.count()) - 1; i >= 0; i--) { await rm.nth(i).click().catch(() => {}); await sleep(300); }
        await page.locator('.o_kanban_record').filter({ hasText: hit.name }).first().scrollIntoViewIfNeeded().catch(() => {}); await settle(page, 800);
        await shot(page, 'm3b-rezerv');
    }
});
// m4: власник/фінансист — маржа замовлення (форма) і звіт собівартості карточками (найнижча маржа — угорі, червоним)
await run('m4', async () => {
    const { page } = await as('owner');
    await go(page, '/odoo/action-sale.action_orders');
    await page.locator('.o_data_row, .o_kanban_record').first().click();
    await settle(page, 1500);
    await tall(page, 'm4t-marzha-tall', 1700);
    await page.getByText(/Маржа/).last().scrollIntoViewIfNeeded().catch(() => {});
    await sleep(600);
    await shot(page, 'm4-marzha');
    await go(page, '/odoo/action-td_mebli_sale.sale_order_line_td_cost_action');
    await settle(page, 1200);
    await shot(page, 'm4b-zvit-marzhi');
    await tall(page, 'm4bt-zvit-marzhi-tall', 1500);
});
// m5: власник/директор — дашборд керівника на телефоні (верх і низ, висока версія, підсвітка карток)
await run('m5', async () => {
    const { page } = await as('owner');
    await go(page, '/odoo/action-td_mebli_dashboard.action_dashboard');
    await page.waitForSelector('.td_dash_grid', { timeout: 20000 });
    await shot(page, 'm5-dashboard');
    await page.evaluate(() => { const el = document.querySelector('.td_dash'); if (el) el.scrollTop = el.scrollHeight; });
    await sleep(500);
    await shot(page, 'm5b-dashboard-nyz');
    await page.evaluate(() => { const el = document.querySelector('.td_dash'); if (el) el.scrollTop = 0; });
    await page.setViewportSize({ width: 390, height: 2300 });
    await settle(page, 1500);
    const rects = await page.evaluate(() => [...document.querySelectorAll('.td_card')].map((c) => { const r = c.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; }));
    fs.writeFileSync(path.join(OUT, 'm5-cards.json'), JSON.stringify(rects));
    await page.screenshot({ path: path.join(OUT, 'm5t-dashboard-tall.png') });
    console.log('shot m5t-dashboard-tall', rects.length, 'cards');
    for (let i = 0; i < rects.length; i++) { // той самий довгий кадр із підсвіченою карткою i
        await page.evaluate((k) => { document.querySelectorAll('.td_card').forEach((c, j) => { c.style.outline = j === k ? '10px solid #FE5000' : ''; c.style.outlineOffset = '-2px'; }); }, i);
        await page.screenshot({ path: path.join(OUT, `m5t-dashboard-hl${i}.png`) });
    }
    await page.evaluate(() => document.querySelectorAll('.td_card').forEach((c) => { c.style.outline = ''; }));
    await page.setViewportSize({ width: 390, height: 844 });
});
await browser.close();
process.exit(failed ? 1 : 0);
