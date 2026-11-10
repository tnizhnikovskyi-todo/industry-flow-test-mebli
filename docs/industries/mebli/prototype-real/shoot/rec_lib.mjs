// Бібліотека живого запису Odoo для відео (Playwright recordVideo): оверлей у сторінці (курсор, натискання/дотики, титри, плашка ToDo,
// count-up цифр, zoom/pan, плавна прокрутка) і допоміжні дії. Інтерфейс Odoo не перефарбовується — стиль ToDo лише в оверлеї.
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import fs from 'fs';
import path from 'path';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const here = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(here, '..');
export const REC = path.join(ROOT, 'video', 'rec');
fs.mkdirSync(REC, { recursive: true });
export const BASE = process.env.BASE || 'http://127.0.0.1:19071';
export const DB = process.env.DB || 'mebli_demo';
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const b64 = (f) => fs.readFileSync(path.join(ROOT, 'brand-todo', f)).toString('base64');
const FONT = `@font-face{font-family:'Open Sans';font-weight:400;src:url(data:font/ttf;base64,${b64('fonts/OpenSans-regular.ttf')})}@font-face{font-family:'Open Sans';font-weight:700;src:url(data:font/ttf;base64,${b64('fonts/OpenSans-bold.ttf')})}`;
const LOGO = 'data:image/png;base64,' + b64('todo-logo.png');

export const DESKTOP = { viewport: { width: 1600, height: 900 }, rec: { width: 1920, height: 1080 } };
export const MOBILE = { viewport: { width: 390, height: 690 }, rec: { width: 780, height: 1380 } };

// ---------------------------------------------------------------- оверлей у сторінці
const OVERLAY = (mobile) => `(() => { const boot = () => {
  if (window.__ov) return; window.__ov = true;
  const M = ${mobile ? 'true' : 'false'};
  const css = document.createElement('style');
  css.textContent = ${JSON.stringify(FONT)} + \`
  #ov-cur{position:fixed;left:0;top:0;width:30px;height:30px;z-index:2147483647;pointer-events:none;display:\${M ? 'none' : 'block'};transform:translate(-100px,-100px);filter:drop-shadow(0 2px 3px rgba(0,0,0,.45))}
  .ov-rip{position:fixed;z-index:2147483646;pointer-events:none;border-radius:50%;border:4px solid #FE5000;background:rgba(254,80,0,.28);width:20px;height:20px;margin:-10px 0 0 -10px;animation:ovrip .6s ease-out forwards}
  .ov-fin{position:fixed;z-index:2147483646;pointer-events:none;border-radius:50%;background:rgba(254,80,0,.45);border:3px solid #fff;width:46px;height:46px;margin:-23px 0 0 -23px;animation:ovfin .7s ease-out forwards}
  @keyframes ovrip{to{transform:scale(\${M ? 3.2 : 4});opacity:0}} @keyframes ovfin{0%{transform:scale(.6);opacity:1}100%{transform:scale(1.5);opacity:0}}
  #ov-title{position:fixed;z-index:2147483645;left:\${M ? 10 : 28}px;\${M ? 'top:54px' : 'bottom:28px'};max-width:\${M ? 370 : 1150}px;background:rgba(16,24,32,.95);color:#fff;border-left:\${M ? 6 : 8}px solid #FE5000;
    border-radius:10px;padding:\${M ? '9px 14px' : '14px 24px'};font-family:'Open Sans',sans-serif;opacity:0;transform:translateY(\${M ? '-24px' : '24px'});transition:opacity .35s,transform .35s;pointer-events:none}
  #ov-title.on{opacity:1;transform:none}
  #ov-title .k{font-size:\${M ? 12 : 16}px;letter-spacing:.07em;text-transform:uppercase;color:#FE5000;font-weight:700;margin-bottom:2px}
  #ov-title .t{font-size:\${M ? 20 : 30}px;font-weight:700;line-height:1.2} #ov-title .t em{font-style:normal;color:#FE5000}
  #ov-badge{position:fixed;z-index:2147483645;right:\${M ? 8 : 28}px;bottom:\${M ? 'auto' : '28px'};top:\${M ? 'auto' : 'auto'};display:none;background:#fff;border-radius:12px;padding:8px 16px;box-shadow:0 2px 10px rgba(0,0,0,.3);pointer-events:none}
  #ov-badge img{height:38px;display:block}
  #ov-pain{position:fixed;z-index:2147483644;left:0;right:0;top:0;bottom:0;background:rgba(16,24,32,.9);color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;
    font-family:'Open Sans',sans-serif;padding:0 \${M ? 24 : 160}px;opacity:0;transition:opacity .4s;pointer-events:none}
  #ov-pain.on{opacity:1} #ov-pain .k{font-size:\${M ? 15 : 24}px;letter-spacing:.08em;text-transform:uppercase;color:#FE5000;font-weight:700;margin-bottom:14px}
  #ov-pain .t{font-size:\${M ? 30 : 58}px;font-weight:700;line-height:1.18} #ov-pain .t em{font-style:normal;color:#FE5000}
  \`;
  document.documentElement.appendChild(css);
  const mk = (id, html) => { const d = document.createElement('div'); d.id = id; if (html) d.innerHTML = html; document.documentElement.appendChild(d); return d; };
  const cur = mk('ov-cur', '<svg viewBox="0 0 24 24" width="30" height="30"><path d="M3 2l17 9-7.5 2L9.5 21z" fill="#fff" stroke="#101820" stroke-width="1.6" stroke-linejoin="round"/></svg>');
  const title = mk('ov-title'); const badge = mk('ov-badge', '<img src="${LOGO}">'); const pain = mk('ov-pain');
  const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;'); const rich = (s) => esc(s).replace(/\\*\\*(.+?)\\*\\*/g, '<em>$1</em>');
  const P = () => { try { return JSON.parse(sessionStorage.getItem('ov_pos') || 'null'); } catch (e) { return null; } };
  const place = (x, y) => { cur.style.transform = 'translate(' + (x - 4) + 'px,' + (y - 2) + 'px)'; };
  let last = 0;
  addEventListener('mousemove', (e) => { place(e.clientX, e.clientY); const n = Date.now(); if (n - last > 120) { last = n; try { sessionStorage.setItem('ov_pos', JSON.stringify([e.clientX, e.clientY])); } catch (x) {} } }, true);
  const rip = (x, y, cls) => { const r = document.createElement('div'); r.className = cls; r.style.left = x + 'px'; r.style.top = y + 'px'; document.documentElement.appendChild(r); setTimeout(() => r.remove(), 800); };
  addEventListener('pointerdown', (e) => { if (e.pointerType === 'touch') rip(e.clientX, e.clientY, 'ov-fin'); else rip(e.clientX, e.clientY, 'ov-rip'); }, true);
  const p0 = P(); if (p0 && !M) place(p0[0], p0[1]);
  window.__title = (k, t) => { title.innerHTML = '<div class="k">' + esc(k) + '</div><div class="t">' + rich(t) + '</div>'; title.classList.remove('on'); void title.offsetWidth; setTimeout(() => title.classList.add('on'), 30); };
  window.__titleOff = () => title.classList.remove('on');
  window.__pain = (k, t) => { pain.innerHTML = '<div class="k">' + esc(k) + '</div><div class="t">' + rich(t) + '</div>'; pain.classList.add('on'); };
  window.__painOff = () => pain.classList.remove('on');
  window.__reveal = (sel, step = 140) => { document.querySelectorAll(sel).forEach((el, i) => { el.style.transition = 'none'; el.style.opacity = '0'; el.style.transform = 'translateY(26px) scale(.96)';
    setTimeout(() => { el.style.transition = 'opacity .5s, transform .5s'; el.style.opacity = '1'; el.style.transform = 'none'; }, 60 + i * step); }); };
  window.__bars = (sel, ms = 1200) => { document.querySelectorAll(sel).forEach((el) => { const w = el.style.width; el.style.transition = 'none'; el.style.width = '0'; void el.offsetWidth;
    setTimeout(() => { el.style.transition = 'width ' + ms + 'ms ease-out'; el.style.width = w; }, 60); }); };
  window.__countUp = (sel, ms = 1400) => { document.querySelectorAll(sel).forEach((el) => {
    const orig = el.textContent; const m = orig.match(/[-+]?\\d[\\d\\s\\u00a0\\u202f]*(?:,\\d+)?/); if (!m) return;
    const num = m[0]; const dec = (num.split(',')[1] || '').length; const val = parseFloat(num.replace(/[\\s\\u00a0\\u202f]/g, '').replace(',', '.')); const plus = num[0] === '+';
    const fmt = (v) => { const [i, f] = Math.abs(v).toFixed(dec).split('.'); return (v < 0 ? '-' : plus ? '+' : '') + i.replace(/\\B(?=(\\d{3})+(?!\\d))/g, ' ') + (f ? ',' + f : ''); };
    const t0 = performance.now(); const tick = (n) => { const k = Math.min(1, (n - t0) / ms); const e = 1 - Math.pow(1 - k, 3); el.textContent = orig.replace(num, fmt(val * e));
      if (k < 1) requestAnimationFrame(tick); else el.textContent = orig; }; requestAnimationFrame(tick); }); };
  window.__zoom = (sel, s = 1.6, ms = 900) => { const c = document.querySelector('.o_action_manager'); const el = document.querySelector(sel); if (!c || !el) return;
    c.style.transition = 'none'; const prev = c.style.transform; c.style.transform = 'none'; const cr = c.getBoundingClientRect(); const r = el.getBoundingClientRect(); c.style.transform = prev; void c.offsetWidth;
    const cx = r.left - cr.left + r.width / 2, cy = r.top - cr.top + r.height / 2;
    const tx = r.width * s > cr.width * .92 ? Math.min(0, -(r.left - cr.left) * s + 6) : Math.min(0, Math.max(cr.width - s * cr.width, cr.width / 2 - s * cx)), ty = Math.min(0, Math.max(cr.height - s * cr.height, cr.height / 2 - s * cy));
    c.style.transformOrigin = '0 0'; c.style.transition = 'transform ' + ms + 'ms cubic-bezier(.45,0,.2,1)'; c.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + s + ')'; };
  window.__zoomOff = (ms = 700) => { const c = document.querySelector('.o_action_manager'); if (!c) return; c.style.transition = 'transform ' + ms + 'ms cubic-bezier(.45,0,.2,1)'; c.style.transform = 'none'; };
  window.__scroll = (sel, to, ms = 1500) => new Promise((res) => { const el = document.querySelector(sel); if (!el) return res(false); const a = el.scrollTop;
    const b = to === 'end' ? el.scrollHeight : to; const t0 = performance.now(); const tick = (n) => { const k = Math.min(1, (n - t0) / ms); const e = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      el.scrollTop = a + (b - a) * e; if (k < 1) requestAnimationFrame(tick); else res(true); }; requestAnimationFrame(tick); });
}; if (document.documentElement) boot(); else new MutationObserver((m, o) => { if (document.documentElement) { o.disconnect(); boot(); } }).observe(document, { childList: true }); })();`;

// ---------------------------------------------------------------- контекст і дії
let browser;
export async function launch() { browser = await chromium.launch(); return browser; }
const cookieFile = path.join(REC, 'cookies.json');
export async function cookiesFor(role) {
    let all = {}; try { all = JSON.parse(fs.readFileSync(cookieFile, 'utf8')); } catch (e) { /* ще немає */ }
    if (all[role]) return all[role];
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const pg = await ctx.newPage();
    await pg.goto(`${BASE}/web/login?db=${DB}`);
    await pg.fill('input[name=login]', `${role}@demo-fabryka.example`);
    await pg.fill('input[name=password]', 'demo');
    await pg.click('button[type=submit]');
    await pg.waitForSelector('.o_navbar, .o_main_navbar', { timeout: 30000 });
    all[role] = await ctx.cookies(); fs.writeFileSync(cookieFile, JSON.stringify(all)); await ctx.close();
    return all[role];
}

// clip('D2', {role:'salon', mobile:false}, async (c) => {...}) -> video/rec/D2.mp4 + D2.json {ss, dur}
// Запис — власний CDP-screencast (Playwright recordVideo не збільшує кадр понад розмір вікна: на телефоні вийшов би 390x640). Кадри JPEG
// у фізичних пікселях (DSF), потім ffmpeg склеює їх за часовими мітками в 30 fps.
import { execFileSync } from 'child_process';
export async function clip(name, { role, mobile = false, url = null, plain = false, dev: devOverride = null }, fn) {
    const dev = devOverride || (mobile ? MOBILE : DESKTOP);
    const dir = fs.mkdtempSync(path.join(REC, 'tmp-'));
    const opts = { viewport: dev.viewport, locale: 'uk-UA', timezoneId: 'Europe/Kyiv', deviceScaleFactor: mobile ? dev.rec.width / dev.viewport.width : 1 };
    if (mobile) Object.assign(opts, { isMobile: true, hasTouch: true });
    const ctx = await browser.newContext(opts);
    if (role) await ctx.addCookies(await cookiesFor(role));
    if (!plain) await ctx.addInitScript(OVERLAY(mobile));
    const page = await ctx.newPage();
    page.setDefaultTimeout(20000);
    page.on('pageerror', (e) => console.error('PAGEERR', name, String(e.message).slice(0, 200)));
    const cdp = await ctx.newCDPSession(page); const frames = []; let writing = Promise.resolve(), stop = false, loop = Promise.resolve();
    const put = (ts, b64d) => { const idx = frames.length; frames.push(ts); writing = writing.then(() => fs.promises.writeFile(path.join(dir, `${String(idx).padStart(6, '0')}.jpg`), Buffer.from(b64d, 'base64'))); };
    if (mobile) { // телефон: цикл знімків у фізичних пікселях (DSF 2 -> 780x1280); screencast віддає лише CSS-розмір
        loop = (async () => { while (!stop) { const t = Date.now() / 1000; try { const r = await page.screenshot({ type: 'jpeg', quality: 88, animations: 'allow', caret: 'initial' }); put(t, r.toString('base64')); } catch (e) { await sleep(50); } } })();
    } else {
        cdp.on('Page.screencastFrame', (f) => { put(f.metadata.timestamp, f.data); cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }).catch(() => {}); });
        await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 92, maxWidth: dev.rec.width, maxHeight: dev.rec.height, everyNthFrame: 1 });
    }
    const tStart = Date.now() / 1000;
    const c = { page, mobile, ready: null, pos: [200, 200], events: [] };
    c.t = () => Date.now() / 1000 - (frames[0] ?? tStart);
    c.mark = () => { if (c.ready === null) c.ready = Date.now() / 1000; };
    if (url) await page.goto(url.startsWith('file:') ? url : BASE + url);
    let err = null;
    try { await fn(c); } catch (e) { err = e; console.error('FAIL', name, String(e.message).split('\n').slice(0, 5).join(' | ')); await page.screenshot({ path: `/tmp/fail-${name}.png` }).catch(() => {}); }
    const endT = Date.now() / 1000;
    await sleep(300); stop = true; await loop; await cdp.send('Page.stopScreencast').catch(() => {}); await writing; await ctx.close();
    // ffconcat за часовими мітками
    const list = []; for (let i = 0; i < frames.length; i++) { list.push(`file '${path.join(dir, String(i).padStart(6, '0') + '.jpg')}'`); list.push(`duration ${Math.max(0.01, (frames[i + 1] ?? frames[i] + 0.3) - frames[i]).toFixed(4)}`); }
    list.push(`file '${path.join(dir, String(frames.length - 1).padStart(6, '0') + '.jpg')}'`);
    fs.writeFileSync(path.join(dir, 'list.txt'), list.join('\n'));
    const out = path.join(REC, `${name}.mp4`);
    execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', path.join(dir, 'list.txt'), '-vf', `fps=30,scale=${dev.rec.width}:${dev.rec.height}:flags=lanczos,format=yuv420p`, '-c:v', 'libx264', '-crf', '17', '-preset', 'veryfast', out]);
    fs.rmSync(dir, { recursive: true, force: true });
    const ss = Math.max(0, (c.ready ?? frames[0]) - frames[0]) + 0.15, dur = endT - (c.ready ?? frames[0]) - 0.3;
    fs.writeFileSync(path.join(REC, `${name}.json`), JSON.stringify({ ss, dur, ok: !err, events: c.events }));
    console.log(err ? 'ПОМИЛКА' : 'ok', name, dur.toFixed(1), 'с,', frames.length, 'кадрів');
    return !err;
}
export async function settle(page, ms = 600) {
    await page.waitForLoadState('load').catch(() => {});
    await page.waitForFunction(() => !document.querySelector('.o_loading, .o_blockUI, .o_ui_blocked'), null, { timeout: 8000 }).catch(() => {});
    // не знімаємо порожній екран: чекаємо на зміст подання (список, дошка, графік, форма, зведена, дашборд)
    await page.waitForSelector('.o_list_renderer, .o_kanban_renderer, .o_graph_renderer canvas, .o_form_view, .o_pivot, .td_dash_grid, .o_content', { timeout: 8000 }).catch(() => {});
    await sleep(ms);
}
export async function goto(c, url, ms = 900) { await c.page.goto(BASE + url); await settle(c.page, ms); }
// Титри НЕ малюються в сторінці (їх зрізало б наближення й монтаж): записуємо момент і текст, а накладає їх montage.mjs (ffmpeg overlay)
export const title = async (c, k, t, short) => { c.events.push({ type: 'title', t: c.t(), k, text: t, short: short || t }); };
export const titleOff = async (c) => { c.events.push({ type: 'off', t: c.t() }); };
export async function pain(c, k, t, ms = 2100) { // біль на весь екран поверх живого Odoo (накладає монтаж), потім зникає
    const t0 = c.t(); await sleep(ms); c.events.push({ type: 'pain', t: t0, t1: c.t(), k, text: t }); await sleep(450);
}
// курсор плавно їде до точки (кадри відео бачать рух, а не стрибок)
export async function glide(c, x, y, ms = 500) {
    const [x0, y0] = c.pos; const n = Math.max(8, Math.round(ms / 20));
    for (let i = 1; i <= n; i++) { const k = i / n, e = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2; await c.page.mouse.move(x0 + (x - x0) * e, y0 + (y - y0) * e); await sleep(ms / n); }
    c.pos = [x, y];
}
async function center(loc) {
    await loc.scrollIntoViewIfNeeded().catch(() => {});
    const b = await loc.boundingBox(); if (!b) throw new Error('немає boundingBox');
    return [b.x + b.width / 2, b.y + b.height / 2];
}
// клік: на десктопі курсор їде й натискає; на телефоні - дотик пальцем
export async function press(c, loc, { pause = 220, settleMs = 700 } = {}) {
    await loc.first().waitFor({ state: 'visible' });
    const [x, y] = await center(loc.first());
    if (c.mobile) { await sleep(pause); await c.page.touchscreen.tap(x, y); }
    else { await glide(c, x, y, 520); await sleep(pause); await c.page.mouse.down(); await sleep(60); await c.page.mouse.up(); }
    await settle(c.page, settleMs);
}
export async function typeIn(c, loc, text, delay = 85) {
    await press(c, loc, { settleMs: 200 });
    await c.page.keyboard.press('Control+A'); await loc.first().pressSequentially(text, { delay }); await sleep(900);
}
export const scroll = (c, sel, to, ms = 1500) => c.page.evaluate(([s, t, m]) => window.__scroll(s, t, m), [sel, to, ms]);
// «пауза з рухом»: курсор повільно дрейфує (десктоп) або сторінка трохи дихає, щоб кадр не був нерухомим
export async function hold(c, ms) {
    const end = Date.now() + ms; let i = 0;
    while (Date.now() < end) {
        if (!c.mobile) { const [x, y] = c.pos; await c.page.mouse.move(x + Math.sin(i / 3) * 18, y + Math.cos(i / 4) * 10); i++; }
        await sleep(110);
    }
}
// на телефоні наближення зрізало б правий край (відсотки): замість нього — плавна прокрутка до елемента
export const zoom = (c, sel, s = 1.6, ms = 900) => c.mobile
    ? c.page.evaluate(([a, d]) => { const el = document.querySelector(a); const sc = el && (el.closest('.td_dash, .o_content, .o_action_manager') || document.scrollingElement); if (!el || !sc) return; const r = el.getBoundingClientRect(); const to = sc.scrollTop + r.top - 70; const a0 = sc.scrollTop, t0 = performance.now(); const tick = (n) => { const k = Math.min(1, (n - t0) / d); sc.scrollTop = a0 + (to - a0) * (k * k * (3 - 2 * k)); if (k < 1) requestAnimationFrame(tick); }; requestAnimationFrame(tick); }, [sel, ms])
    : c.page.evaluate(([a, b, d]) => window.__zoom(a, b, d), [sel, s, ms]);
export const zoomOff = (c, ms = 700) => c.page.evaluate((m) => window.__zoomOff(m), ms);
// прокрутка першого елемента, що справді прокручується (контейнер залежить від подання й ширини екрана); to: число px або 'end'
export const scrollAny = (c, to, ms = 1500) => c.page.evaluate(([to, ms]) => new Promise((res) => {
    const cand = [...document.querySelectorAll('.o_form_view_container, .o_content, .o_form_sheet_bg, .o_kanban_renderer, .o_action_manager, .td_dash, .o_form_view, .o_view_controller, main, body, html')];
    const el = cand.find((e) => e.scrollHeight > e.clientHeight + 30 && /auto|scroll/.test(getComputedStyle(e).overflowY)) || document.scrollingElement;
    const a = el.scrollTop, b = to === 'end' ? el.scrollHeight : to, t0 = performance.now();
    const tick = (n) => { const k = Math.min(1, (n - t0) / ms), e = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2; el.scrollTop = a + (b - a) * e; if (k < 1) requestAnimationFrame(tick); else res(true); };
    requestAnimationFrame(tick);
}), [to, ms]);
