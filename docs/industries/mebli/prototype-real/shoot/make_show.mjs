// SHOW.tpl.md + shoot/facts.json (з зйомки) -> SHOW.md, SHOW.html (стиль ToDo) і SHOW.pdf (Playwright). Запуск: node make_show.mjs
// Формат шаблону: `# Заголовок` + вступ; далі блоки `## Назва` (абзаци: **Біль:** / **Вигода:** / **Як це в Odoo:**, картинки) і блок `## Заклик`.
import { createRequire } from 'module';
import { fileURLToPath, pathToFileURL } from 'url';
import fs from 'fs'; import path from 'path';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const here = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(here, '..');
const facts = JSON.parse(fs.readFileSync(path.join(here, 'facts.json'), 'utf8'));
const bad = (facts.checks || []).filter((c) => !c.ok);
if (bad.length) { console.error('Числа не збігаються з кадрами:', JSON.stringify(bad)); process.exit(1); }

if (!facts.dash.cards.margin.value.startsWith(String(facts.margin_weighted).replace('.', ','))) { console.error('Маржа звіту й дашборда розходяться:', facts.margin_weighted, facts.dash.cards.margin.value); process.exit(1); }
const D = facts.dash.cards, nb = (s) => String(s).replace(/ /g, ' ').replace('₴', 'грн'); // ₴ немає в Open Sans: у документі — «грн»
const lines = (c) => c.lines || [];
const loads = facts.loads || [];
const over = loads.filter((l) => l.pct > 100).reverse(), within = loads.filter((l) => l.pct <= 100);
const nm = (l) => l.name.toLowerCase();
const loadText = (over.length ? over.map((l) => `${nm(l)} — ${l.pct}%`).join(', ') + ' (червоним), ' : '') + (within.length ? `решта — ${within[0].pct}–${within[within.length - 1].pct}%` : '');
const num = (s) => parseInt(String(s).replace(/\D+/g, '') || '0', 10);
const pl = (n, a, b, c) => { const m10 = n % 10, m100 = n % 100; return m10 === 1 && m100 !== 11 ? a : (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) ? b : c; };
const f1 = (x) => x.toFixed(1).replace('.', ',');
const _o = num(lines(D.revenue)[0].replace(/\(.*\)/, '').replace(/.*: /, '')), _l = num((D.margin.alert || '').replace(/.*: /, ''));
const vars = {
    d_orders_txt: `${_o} ${pl(_o, 'замовлення', 'замовлення', 'замовлень')}`, d_low_txt: `${_l} ${pl(_l, 'замовлення', 'замовлення', 'замовлень')}`,
    d_revenue: nb(D.revenue.value), d_revenue_delta: nb(D.revenue.delta.text).replace(/^\S+\s/, ''), d_orders: lines(D.revenue)[0].replace(/\(.*\)/, '').replace(/.*: /, '').trim(),
    d_margin: D.margin.value, d_margin_delta: D.margin.delta.text.replace(/^\S+\s/, ''), d_low: (D.margin.alert || '').replace(/.*: /, ''), d_low_text: D.margin.alert || '',
    d_launch: D.launch.value, d_launch_delta: D.launch.delta.text.replace(/^\S+\s/, ''), d_load: loadText, d_top: D.load.rows.filter((r) => r.over).map((r) => `«${r.name}» ${r.pct}%`).join(', ') || '—',
    d_waste: D.cutting.value, d_saving: nb(lines(D.cutting)[0].replace(/.*: /, '')), d_overrun: D.plan_fact.value, d_plan: nb(D.plan_fact.plan), d_fact: nb(D.plan_fact.fact),
    m_avg: (facts.margin_weighted ?? '').toString().replace('.', ','), cut_m2: facts.cut_m2, cut_saving: facts.cut_saving, cut_waste: facts.cut_waste,
    plan_cost: nb(facts.plan_cost), real_cost: nb(facts.real_cost), avg_launch: facts.avg_launch, tests: process.env.TESTS || '38', load_text: loadText,
};
let md = fs.readFileSync(path.join(ROOT, 'SHOW.tpl.md'), 'utf8').replace(/\{\{(\w+)\}\}/g, (_, k) => { if (vars[k] === undefined) throw new Error('немає факту ' + k); return vars[k]; });
fs.writeFileSync(path.join(ROOT, 'SHOW.md'), md);

// md -> html: hero (# + вступ + три цифри дашборда), блоки «текст зліва — скриншот справа», заклик
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const inline = (s) => esc(s).replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img alt="$1" src="$2">').replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
const sections = []; let cur = { title: null, h1: null, paras: [], imgs: [], list: [] };
for (const raw of md.split('\n')) {
    const line = raw.trim();
    const h = /^(#{1,2}) (.*)/.exec(line);
    if (h) { sections.push(cur); cur = { title: h[2], h1: h[1] === '#', paras: [], imgs: [], list: [] }; continue; }
    if (/^!\[/.test(line)) { cur.imgs.push(...line.split(/(?<=\))(?=!\[)/)); continue; }
    if (/^[-*] /.test(line)) { cur.list.push(line.replace(/^[-*] /, '')); continue; }
    if (line) cur.paras.push(line);
}
sections.push(cur);
const body = sections.filter((s) => s.title).map((s) => {
    if (s.h1) {
        const big = [[D.revenue.value, 'виручка за 30 днів', D.revenue.delta.text], [D.margin.value, 'середня маржа', D.margin.alert || D.margin.delta.text], [D.launch.value, 'від замовлення до запуску', D.launch.target]];
        return `<section class="hero"><h1>${inline(s.title)}</h1>${s.paras.map((p) => `<p class="lead">${inline(p)}</p>`).join('')}
          <div class="big">${big.map(([v, l, n]) => `<div><b>${esc(nb(v))}</b><span>${esc(l)}</span><i>${esc(nb(n))}</i></div>`).join('')}</div>${s.imgs.map(inline).join('')}</section>`;
    }
    if (/^Заклик/.test(s.title)) {
        return `<section class="cta"><h2>${inline(s.paras[0] || 'Покажемо на ваших даних')}</h2>${s.paras.slice(1).map((p) => `<p>${inline(p)}</p>`).join('')}<div class="site">todo.ltd</div></section>`;
    }
    return `<section class="blk"><div class="txt"><h2>${inline(s.title)}</h2>${s.paras.map((p) => `<p>${inline(p)}</p>`).join('')}${s.list.length ? `<ul>${s.list.map((l) => `<li>${inline(l)}</li>`).join('')}</ul>` : ''}</div>${[s.imgs.filter((x) => !/screens-mobile/.test(x)), s.imgs.filter((x) => /screens-mobile/.test(x))].map((g, i) => g.length ? `<div class="img${i ? ' mob' : ''}">${g.map(inline).join('')}</div>` : '').join('')}</section>`;
}).join('\n');
const doc = `<!doctype html><html lang="uk"><head><meta charset="utf-8"><title>Меблева фабрика на Odoo — ToDo</title>
<link rel="stylesheet" href="shoot/brand.css"><style>
@page { size: A4; margin: 14mm 12mm 16mm; }
body { color: #101820; font-size: 10pt; line-height: 1.45; max-width: 186mm; margin: 0 auto; }
*, code, pre, kbd, b, strong, i, em, span, h1, h2, p, li { font-family: 'Open Sans', sans-serif !important; }
header.top { display: flex; align-items: center; justify-content: space-between; border-bottom: 4px solid #FE5000; padding-bottom: 6px; margin-bottom: 10px; }
header.top img { height: 36px; } header.top span { color: #808080; font-size: 9.5pt; }
.hero h1 { font-size: 24pt; line-height: 1.12; margin: .1em 0 .25em; } .hero .lead { font-size: 12pt; color: #101820; margin: 0 0 8px; }
.big { display: flex; gap: 10px; margin: 10px 0 8px; } .big div { flex: 1; background: #101820; color: #fff; border-radius: 8px; padding: 10px 12px; border-left: 6px solid #FE5000; }
.big b { display: block; font-size: 20pt; line-height: 1.1; } .big span { display: block; color: #BFBFBF; font-size: 9pt; text-transform: uppercase; letter-spacing: .04em; } .big i { display: block; font-style: normal; font-size: 9pt; color: #FE5000; margin-top: 4px; font-weight: 700; }
.hero img { width: 100%; border: 1px solid #BFBFBF; border-radius: 6px; }
.blk { display: block; margin: 12px 0; padding-top: 8px; border-top: 1px solid #e5e5e5; }
.blk .txt { break-inside: avoid; break-after: avoid; }
.blk h2 { font-size: 12.5pt; margin: 0 0 4px; border-left: 6px solid #FE5000; padding-left: 8px; line-height: 1.2; }
.blk p { margin: 4px 0; } .blk ul { margin: 4px 0; padding-left: 16px; } .blk b { color: #101820; }
.blk .img { break-inside: avoid; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 8px; align-items: start; } .blk .img img { display: block; width: 100%; max-width: 100%; height: auto; object-fit: contain; border: 1px solid #BFBFBF; border-radius: 4px; break-inside: avoid; }
.blk .img img:not(:first-child):not([src*='screens-mobile']) { aspect-ratio: 16 / 10; object-fit: cover; object-position: center 35%; }
.blk .img img:first-child:nth-last-child(1) { grid-column: 1 / -1; }
.blk .img:has(img:nth-child(3)) { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.blk .img img[src*='screens/'] { aspect-ratio: 16 / 10; object-fit: cover; object-position: center 30%; }
.blk .img.mob { grid-template-columns: repeat(4, minmax(0, 1fr)); } .blk .img img[src*='screens-mobile'] { width: 100%; height: auto; border-radius: 10px; grid-column: auto !important; }
.cta { margin-top: 14px; padding: 18px 20px; background: #101820; color: #fff; border-radius: 10px; border-top: 8px solid #FE5000; text-align: center; break-inside: avoid; }
.cta h2 { font-size: 17pt; margin: 0 0 6px; } .cta p { margin: 4px 0; color: #BFBFBF; } .cta .site { display: inline-block; margin-top: 8px; background: #FE5000; color: #fff; font-weight: 700; font-size: 18pt; padding: 4px 22px; border-radius: 999px; }

/* компактна верстка: текст ліворуч (~30%), один великий скриншот праворуч (~65%), мобільні — у рамці телефона в ряд; футер із логотипом на кожній сторінці */
@page { margin: 12mm 12mm 18mm; }
.blk { display: grid; grid-template-columns: 72mm minmax(0, 1fr); gap: 3mm 5mm; align-items: start; margin: 4px 0; padding-top: 6px; break-inside: avoid; }
.blk:not(:has(.img.mob)) { break-inside: auto; } .blk .img, .blk .txt { break-inside: avoid; }
.blk .txt { break-after: auto; } .blk .img { margin-top: 0; grid-template-columns: minmax(0, 1fr) !important; }
.blk .img:not(.mob) img { aspect-ratio: auto !important; object-fit: contain !important; height: auto; }
.blk .img:not(.mob) img:nth-child(n+2) { display: none; } .blk .img:not(.mob) { max-width: 104mm; }
.blk:has(.img.mob) { grid-template-columns: 1fr; } .blk .img.mob { grid-template-columns: repeat(4, 31mm) !important; gap: 8mm; padding: 0; justify-content: center; } .blk .img.mob img { display: block !important; border: 5px solid #0b0f14 !important; border-radius: 16px !important; box-shadow: 0 0 0 2px #2a333d, 0 3px 10px rgba(0,0,0,.25); }
.hero img { max-height: 118mm; object-fit: contain; display: block; margin: 0 auto; }
.blk:has(.img.mob:not(:has(img:nth-child(3)))) { grid-template-columns: 70mm minmax(0, 1fr); } .blk .img.mob:not(:has(img:nth-child(3))) { grid-template-columns: repeat(2, 40mm) !important; justify-content: start; }
.cta { break-before: avoid; }
</style></head><body><header class="top"><img src="brand-todo/todo-logo.png"><span>ToDo — впровадження Odoo для виробництв</span></header>${body}</body></html>`;
fs.writeFileSync(path.join(ROOT, 'SHOW.html'), doc.replace(/[▲▼■]\s*/g, ''));
const browser = await chromium.launch(); const page = await browser.newPage();
await page.goto(pathToFileURL(path.join(ROOT, 'SHOW.html')).href); await page.evaluate(() => document.fonts.ready);
const logo64 = 'data:image/png;base64,' + fs.readFileSync(path.join(ROOT, 'brand-todo', 'todo-logo.png')).toString('base64');
await page.pdf({ path: path.join(ROOT, 'SHOW.pdf'), format: 'A4', printBackground: true, preferCSSPageSize: true, displayHeaderFooter: true, headerTemplate: '<span></span>',
    footerTemplate: `<div style="width:100%;margin:0 12mm;padding-top:2mm;border-top:2px solid #FE5000;display:flex;align-items:center;justify-content:space-between;font-family:sans-serif;font-size:8pt;color:#808080"><img src="${logo64}" style="height:7mm"><span>ToDo — впровадження Odoo для виробництв · <b style="color:#FE5000">todo.ltd</b> · розкрій у показі — імітація, дані вигадані</span><span><span class="pageNumber"></span>/<span class="totalPages"></span></span></div>` });
await browser.close(); console.log('SHOW.md/html/pdf готово');
