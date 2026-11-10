// Сценарій показу пакета «меблі» в справжньому Odoo 19 (PLAN.md §6). Запуск: node scenario.mjs [порт]
// Env: BASE (http://127.0.0.1:18069), DB (mebli_demo), STOP_AT (номер кроку, після якого зупинитись).
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const __dirname = path.dirname(fileURLToPath(import.meta.url));

const ROOT = path.resolve(__dirname, '..');
const BASE = process.env.BASE || `http://127.0.0.1:${process.argv[2] || 18069}`;
const DB = process.env.DB || 'mebli_demo';
const STOP_AT = parseInt(process.env.STOP_AT || '99', 10);
const SHOTS = path.join(ROOT, 'screens');
const VIDEO = path.join(ROOT, 'video');
fs.mkdirSync(SHOTS, { recursive: true });
fs.mkdirSync(VIDEO, { recursive: true });

let page;
let n = 0;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const T0 = Date.now();
async function settle(ms = 700) {
    await page.waitForLoadState('load').catch(() => {});
    await page.waitForFunction(() => !document.querySelector('.o_loading, .o_blockUI, .o_ui_blocked'), null, { timeout: 8000 }).catch(() => {});
    await sleep(ms);
}
async function shot(name) {
    n += 1;
    const file = path.join(SHOTS, `${String(n).padStart(2, '0')}-${name}.png`);
    await settle(500);
    await page.screenshot({ path: file });
    console.log('shot', path.basename(file), new Date().toISOString());
}
// Кнопка/вкладка/пункт за видимим текстом (uk або en).
async function clickText(selector, re, opts = {}) {
    const loc = page.locator(selector).filter({ hasText: re }).first();
    await loc.waitFor({ state: 'visible', timeout: 15000 });
    await loc.click(opts);
    await settle();
}
// Меню Odoo: [секція, пункт] за xmlid.
async function menu(sectionXmlid, itemXmlid) {
    if (sectionXmlid) {
        await page.locator(`.o_menu_sections [data-menu-xmlid="${sectionXmlid}"]`).first().click();
        await sleep(300);
    }
    await page.locator(`[data-menu-xmlid="${itemXmlid}"]`).first().click();
    await settle();
}
async function openApp(xmlid) {
    await page.locator('.o_navbar_apps_menu button, .o_menu_toggle').first().click();
    await sleep(300);
    await page.locator(`.o-dropdown--menu [data-menu-xmlid="${xmlid}"], .o_app[data-menu-xmlid="${xmlid}"]`).first().click();
    await settle();
}
async function notebookTab(re) {
    await clickText('.o_notebook .nav-link', re);
}
async function statButton(re) {
    await clickText('.o-form-buttonbox .oe_stat_button', re);
}
async function search(text) {
    const input = page.locator('.o_searchview_input');
    await input.fill(text);
    await input.press('Enter');
    await settle();
}



async function steps() {
    // Вхід
    await page.goto(`${BASE}/web/login?db=${DB}`);
    await page.fill('input[name=login]', 'admin');
    await page.fill('input[name=password]', 'admin');
    await page.click('button[type=submit]');
    await page.waitForSelector('.o_navbar');
    await settle();

    // 01 Виріб «Шафа-купе»
    await openApp('sale.sale_menu_root');
    await menu('sale.product_menu_catalog', 'sale.menu_product_template_action');
    await search('Шафа-купе');
    await page.locator('.o_data_row, .o_kanban_record').filter({ hasText: /Шафа-купе/ }).first().click();
    await settle();
    await notebookTab(/Атрибути|Attributes/);
    await shot('product-attributes');
    await notebookTab(/Деталі виробу/);
    await shot('product-form');
    if (STOP_AT === 1) return;

    // 02 Нове замовлення і конфігуратор
    await menu('sale.sale_order_menu', 'sale.menu_sale_quotations');
    await page.locator('.o_list_button_add, .o-kanban-button-new').first().click();
    await settle();
    await page.locator('.o_field_widget[name=partner_id] input').fill('Салон');
    await page.locator('ul.ui-autocomplete > li > a').first().click();
    await settle();
    await page.locator('a:has-text("Додати товар"), a:has-text("Add a product")').first().click();
    await page.locator('div[name="product_template_id"] input').fill('Шафа-купе');
    await page.locator('ul.ui-autocomplete > li > a').filter({ hasText: /Шафа-купе/ }).first().click();
    await page.waitForSelector('.o_sale_product_configurator_dialog');
    await settle();
    const dlg = page.locator('.o_sale_product_configurator_dialog');
    const ptal = (label) => dlg.locator('div[name="ptal"]').filter({ has: page.locator('label', { hasText: label }) });
    await ptal('Декор корпусу').locator('span', { hasText: 'Kronvald K101' }).first().click();
    await ptal('Декор фасаду').locator('span', { hasText: 'Kronvald K190' }).first().click();
    await ptal('Кромка').locator('span', { hasText: 'ПВХ 2 мм' }).first().click();
    await ptal('Фурнітура').locator('span', { hasText: 'Преміум' }).first().click();
    for (const [label, value] of [['Ширина', '1800'], ['Висота', '2400'], ['Глибина', '600']]) {
        const inp = ptal(label).locator('input[type="text"]');
        await inp.fill(value);
        await dlg.locator('.modal-body').click({ position: { x: 5, y: 5 } });
        await settle(300);
    }
    await shot('configurator');
    await dlg.locator('button', { hasText: /Підтвердити|Confirm/ }).click();
    await page.waitForSelector('.o_sale_product_configurator_dialog', { state: 'detached' });
    await settle(1000);
    // 03 Чернетка замовлення: ціна з коефіцієнтом розміру і маржа
    await shot('sale-order-draft');
    // зберегти замовлення; сформувати специфікацію з рядка
    await page.locator('.o_form_button_save').click();
    await settle(1200);
    if (STOP_AT === 2) return;

    // 04 Специфікація під замовлення
    await page.locator('.o_data_row button:has(.fa-cogs)').click();
    await settle(1500);
    await shot('order-bom');
    await notebookTab(/Деталі/);
    await shot('order-bom-parts');
    if (STOP_AT === 3) return;

    // 05 Назад у замовлення: планова собівартість і маржа рядка
    await page.locator('.breadcrumb-item:not(.active)').last().click();
    await settle(1500);
    await page.locator('.o_optional_columns_dropdown_toggle').first().click();
    await sleep(400);
    for (const re of [/Маржа/, /Собівартість/]) {
        const box = page.locator('.o-dropdown--menu .dropdown-item').filter({ hasText: re });
        for (let i = 0; i < await box.count(); i++) {
            const cb = box.nth(i).locator('input[type=checkbox]');
            if (!(await cb.isChecked())) await cb.click();
        }
    }
    await page.keyboard.press('Escape');
    await settle(800);
    await page.locator('.o_list_renderer').evaluate((el) => { el.scrollLeft = el.scrollWidth; });
    await sleep(400);
    await shot('sale-order-margin');
    await page.locator('.o_list_renderer').evaluate((el) => { el.scrollLeft = 0; });
    if (STOP_AT === 4) return;

    // 06 Підтвердження замовлення
    await page.locator('button[name="action_confirm"]').first().click();
    await settle(2500);
    await shot('sale-confirmed');
    if (STOP_AT === 5) return;

    // 07 Виробниче замовлення
    await page.locator('.o-form-buttonbox .oe_stat_button').filter({ hasText: /Виробництв|Виготовлен/ }).first().click();
    await settle(2000);
    await shot('mo-form');
    await notebookTab(/Робочі|Операц/);
    await shot('mo-workorders');
    if (STOP_AT === 6) return;

    // 08 Дільниці
    await openApp('mrp.menu_mrp_root');
    await menu('mrp.menu_mrp_configuration', 'mrp.menu_view_resource_search_mrp');
    await page.locator('button.o_switch_view.o_kanban').click();
    await settle(1000);
    await shot('workcenters');
    await menu('mrp.menu_mrp_manufacturing', 'mrp.menu_mrp_workorder_todo');
    await page.locator('.o_searchview_dropdown_toggler').click();
    await clickText('.o_search_bar_menu .o_menu_item, .o-dropdown--menu .dropdown-item', /Робочий центр|Робочі центри/);
    await page.keyboard.press('Escape');
    await settle(800);
    for (let i = 0; i < 4; i++) await page.locator('.o_group_header').nth(i).click().then(() => sleep(400));
    await shot('workorders-by-workcenter');
    if (STOP_AT === 7) return;

    // 09 Технолог: МО дня -> завдання розкрою
    await menu('mrp.menu_mrp_manufacturing', 'mrp.menu_mrp_production_action');
    await page.locator('.o_list_renderer thead .o_list_record_selector input').click();
    await page.locator('.o_cp_action_menus button').filter({ hasText: /Дії/ }).click();
    await clickText('.o-dropdown--menu .o_menu_item, .o-dropdown--menu .dropdown-item', /Створити завдання розкрою/);
    await settle(2000);
    await shot('cutting-job-parts');
    await clickText('.o_statusbar_buttons button', /Передати на розкрій/);
    await settle(1500);
    await shot('cutting-job-sent');
    if (STOP_AT === 8) return;

    // 10 Результат розкрою (імітація)
    await clickText('.o_statusbar_buttons button', /Отримати результат/);
    await settle(2000);
    await shot('cutting-result');
    if (STOP_AT === 9) return;
}

(async () => {
    const browser = await chromium.launch();
    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 1,
        recordVideo: { dir: VIDEO, size: { width: 1440, height: 900 } },
    });
    page = await context.newPage();
    browser.on('disconnected', () => console.error('BROWSER DISCONNECTED'));
    page.on('close', () => console.error('PAGE CLOSED at', new Date().toISOString()));
    page.setDefaultTimeout(20000);
    page.on('crash', () => console.error('PAGE CRASH'));
    page.on('pageerror', (e) => console.error('PAGEERR', String(e).slice(0, 200)));
    let failed = null;
    try {
        await steps();
    } catch (e) {
        failed = e;
        await page.screenshot({ path: '/tmp/claude-0/fail.png' }).catch(() => {});
        console.error('STACK', e.stack.split('\n').slice(0,6).join(' / ')); console.error('FAIL', e.message.split('\n').slice(0, 8).join('\n'));
    }
    const video = page.video();
    await context.close();
    if (video) fs.renameSync(await video.path(), path.join(VIDEO, 'scenario.webm'));
    await browser.close();
    process.exit(failed ? 1 : 0);
})();
