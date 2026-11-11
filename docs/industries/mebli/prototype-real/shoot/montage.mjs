// Динамічний монтаж двох відео з ЖИВИХ записів екрана Odoo (video/rec/*.mp4 + .json із подіями титрів): короткі фрагменти,
// плавні переходи ffmpeg xfade, тиха ambient-доріжка. Титри, плашка логотипа ToDo й рамка телефона накладаються ТУТ (прозорі PNG, Open Sans),
// а не в сторінку: наближення/кроп їх не зачіпає. Використання: node montage.mjs [full|reels|all]
import fs from 'fs'; import os from 'os'; import path from 'path';
import { execFileSync } from 'child_process';
import { createRequire } from 'module';
import { fileURLToPath, pathToFileURL } from 'url';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const here = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(here, '..');
const REC = path.join(ROOT, 'video', 'rec');
const BR = path.join(ROOT, 'brand-todo');
const FONT = path.join(BR, 'fonts/OpenSans-bold.ttf');
const FONT_R = path.join(BR, 'fonts/OpenSans-regular.ttf');
const tmp = fs.mkdtempSync(path.join(process.env.TMPDIR || os.tmpdir(), 'mebli-mont-'));
const ff = (args) => execFileSync('ffmpeg', ['-v', 'error', '-y', ...args], { stdio: ['ignore', 'inherit', 'inherit'] });
const probe = (f) => parseFloat(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).toString());
const meta = (n) => JSON.parse(fs.readFileSync(path.join(REC, `${n}.json`), 'utf8'));
let seq = 0; const out = (ext = 'mp4') => path.join(tmp, `p${String(seq++).padStart(3, '0')}.${ext}`);
const wrap = (s, n) => { const w = s.split(' '); const L = []; let cur = ''; for (const x of w) { if ((cur + ' ' + x).trim().length > n) { L.push(cur.trim()); cur = x; } else cur = cur + ' ' + x; } L.push(cur.trim()); return L.join('\n'); };
const txt = (s) => { const f = out('txt'); fs.writeFileSync(f, s); return f.replace(/\\/g, '/').replace(/:/g, '\\:'); };
const X264 = ['-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p'];
const WARN = [];

// ---------------------------------------------------------------- прозорі PNG: титри, плашка, рамка телефона
const d64 = (f, m) => `data:${m};base64,` + fs.readFileSync(f).toString('base64');
const FONTCSS = `@font-face{font-family:'Open Sans';font-weight:400;src:url(${d64(FONT_R, 'font/ttf')})}@font-face{font-family:'Open Sans';font-weight:700;src:url(${d64(FONT, 'font/ttf')})}`;
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
const rich = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, '<em>$1</em>');
let browser;
async function png(html, w, h, file) {
    const pg = await browser.newPage({ viewport: { width: w, height: h } });
    await pg.setContent(`<html><head><style>${FONTCSS}html,body{margin:0;background:transparent;font-family:'Open Sans',sans-serif}em{font-style:normal;color:#FE5000}</style></head><body>${html}</body></html>`);
    await pg.evaluate(() => document.fonts.ready);
    await pg.screenshot({ path: file, omitBackground: true }); await pg.close(); return file;
}
const cache = new Map();
async function img(key, fn) { if (!cache.has(key)) cache.set(key, await fn(path.join(tmp, `i${cache.size}.png`))); return cache.get(key); }
// титр для 16:9: нижня смуга ліворуч
const titleDesk = (k, t) => img('td' + k + t, (f) => png(`<div style="position:absolute;left:48px;bottom:46px;max-width:1300px;background:rgba(16,24,32,.95);color:#fff;border-left:10px solid #FE5000;border-radius:12px;padding:16px 30px 18px">
  <div style="font-size:21px;letter-spacing:.07em;text-transform:uppercase;color:#FE5000;font-weight:700;margin-bottom:4px">${esc(k)}</div><div style="font-size:42px;font-weight:700;line-height:1.2">${rich(t)}</div></div>`, 1920, 1080, f));
// «біль» на весь екран поверх живого Odoo
const painDesk = (k, t) => img('pd' + k + t, (f) => png(`<div style="position:absolute;inset:0;background:rgba(16,24,32,.9);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:0 200px">
  <div style="font-size:30px;letter-spacing:.08em;text-transform:uppercase;color:#FE5000;font-weight:700;margin-bottom:22px">${esc(k)}</div><div style="font-size:70px;font-weight:700;line-height:1.18;color:#fff">${rich(t)}</div></div>`, 1920, 1080, f));
// плашка логотипа ToDo: за розміром логотипа (2277x891), з полями й закругленням
const badge = (h) => img('bd' + h, (f) => png(`<div style="display:inline-block;background:#fff;border-radius:${Math.round(h * .3)}px;padding:${Math.round(h * .22)}px ${Math.round(h * .38)}px;box-shadow:0 3px 14px rgba(0,0,0,.35)"><img src="${d64(path.join(BR, 'todo-logo.png'), 'image/png')}" style="height:${h}px;display:block"></div>`, Math.round(h * 2.56 + h * .76) + 12, Math.round(h * 1.44) + 12, f));
// титр Reels: великий, у безпечній зоні (250..1670), над телефоном
const titleReel = (k, t) => img('tr' + k + t, (f) => png(`<div style="position:absolute;left:0;right:0;top:350px;height:176px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:0 50px;color:#fff">
  <div style="font-size:28px;letter-spacing:.08em;text-transform:uppercase;color:#FE5000;font-weight:700;margin-bottom:4px">${esc(k)}</div><div style="font-size:60px;font-weight:700;line-height:1.1">${rich(t)}</div></div>`, 1080, 1920, f));
// фон Reels: темний ToDo із м'яким помаранчевим сяйвом по боках
const bgReel = () => img('bgr', (f) => png(`<div style="position:absolute;inset:0;background:radial-gradient(55% 28% at 0% 55%,rgba(254,80,0,.30),transparent 70%),radial-gradient(55% 28% at 100% 80%,rgba(254,80,0,.22),transparent 70%),#101820"></div>`, 1080, 1920, f));
// рамка телефона (нейтральна, CSS) з прозорим «екраном»
const phoneFrame = (w, h, b) => img(`pf${w}x${h}`, (f) => { const R = Math.round(w * .11) + b, r = Math.round(w * .11), W = w + 2 * b, H = h + 2 * b;
    const rr = (x, y, ww, hh, q) => `M${x + q},${y}H${x + ww - q}A${q},${q} 0 0 1 ${x + ww},${y + q}V${y + hh - q}A${q},${q} 0 0 1 ${x + ww - q},${y + hh}H${x + q}A${q},${q} 0 0 1 ${x},${y + hh - q}V${y + q}A${q},${q} 0 0 1 ${x + q},${y}Z`;
    return png(`<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" style="position:absolute;left:0;top:0"><path fill-rule="evenodd" fill="#0b0f14" d="${rr(0, 0, W, H, R)} ${rr(b, b, w, h, r)}"/>
    <path fill="none" stroke="#2a333d" stroke-width="3" d="${rr(1.5, 1.5, W - 3, H - 3, R)}"/></svg>
    <div style="position:absolute;left:50%;top:${Math.round(b * .3)}px;width:${Math.round(w * .22)}px;height:${Math.round(b * .35)}px;margin-left:-${Math.round(w * .11)}px;background:#1b232c;border-radius:99px"></div>`, W, H, f); });

// маска екрана: заокруглений прямокутник (білий на чорному) — запис обрізається по внутрішньому вікну рамки
const screenMask = (w, h) => img(`mk${w}x${h}`, (f) => { const r = Math.round(w * .11); return png(`<div style="position:absolute;inset:0;background:#000"><div style="position:absolute;inset:0;background:#fff;border-radius:${r}px"></div></div>`, w, h, f); });

// ---------------------------------------------------------------- накладання PNG із плавним з'явленням у проміжку [s,e] (с шматка)
function overlays(base, items, W, H) { // items: {file,s,e}; повертає {inputs, graph, last}
    const inputs = [], g = []; let last = base;
    items.forEach((it, i) => {
        const D = Math.max(0.5, it.e - it.s);
        inputs.push('-loop', '1', '-framerate', '30', '-t', D.toFixed(2), '-i', it.file);
        const idx = it.idx;
        g.push(`[${idx}:v]format=rgba,fade=t=in:st=0:d=0.2:alpha=1,fade=t=out:st=${Math.max(0.1, D - 0.2).toFixed(2)}:d=0.2:alpha=1,setpts=PTS+${it.s.toFixed(2)}/TB[o${i}]`);
        g.push(`[${last}][o${i}]overlay=${it.x ?? 0}:${it.y ?? 0}:eof_action=pass[l${i}]`); last = `l${i}`;
    });
    return { inputs, graph: g.join(';'), last };
}
// події запису -> проміжки в шматку
function spans(m, a, len, speed) {
    const t0 = m.ss + a, t1 = t0 + len * speed; const ev = (m.events || []).slice().sort((x, y) => x.t - y.t);
    const res = [];
    ev.forEach((e, i) => {
        if (e.type === 'title') {
            const nxt = ev.slice(i + 1).find((x) => x.type === 'title' || x.type === 'off'); const end = Math.min(nxt ? nxt.t : t1, t1);
            if (end > t0 && e.t < t1) res.push({ kind: 'title', e, s: Math.max(0, (e.t - t0) / speed), end: (end - t0) / speed - (nxt && nxt.type === 'title' && nxt.t < t1 ? 0.3 : 0) });
        } else if (e.type === 'pain' && e.t1 > t0 && e.t < t1) res.push({ kind: 'pain', e, s: Math.max(0, (e.t - t0) / speed), end: Math.min(len, (e.t1 + 0.3 - t0) / speed) });
    });
    return res;
}

// ---------------------------------------------------------------- шматки
let zdir = 0;
// десктоп 16:9: запис «дихає» (масштаб 0.93 -> 1.0 або назад) на темному тлі ToDo — нічого з інтерфейсу не обрізається
async function pieceDesk(src, a, len, speed = 1) {
    const m = meta(src), o = out(); const t = len * speed; zdir++;
    const s0 = zdir % 2 ? 0.93 : 1.0, s1 = zdir % 2 ? 1.0 : 0.93;
    const sp = spans(m, a, len, speed); const items = []; let idx = 2;
    for (const x of sp) {
        const file = x.kind === 'pain' ? await painDesk(x.e.k, x.e.text) : await titleDesk(x.e.k, x.e.text);
        const shown = x.end - x.s; if (x.kind === 'title' && shown < 1.5) WARN.push(`${src}: титр «${x.e.text.slice(0, 30)}» ${shown.toFixed(2)} с < 1,5`);
        items.push({ file, s: x.s, e: x.end, idx: idx++ });
    }
    const b = await badge(40); const bi = idx++;
    const ov = overlays('a', items, 1920, 1080);
    const fc = `color=c=0x101820:s=1920x1080:r=30:d=${len.toFixed(2)}[bg];` +
        `[0:v]setpts=(PTS-STARTPTS)/${speed},fps=30,scale=w='1920*(${s0}+(${s1}-${s0})*t/${len.toFixed(2)})':h=-2:eval=frame:flags=bicubic[v];` +
        `[bg][v]overlay=x='(W-w)/2':y='(H-h)/2':shortest=1[a];` + (ov.graph ? ov.graph + ';' : '') +
        `[${ov.last}][${bi}:v]overlay=W-w-34:H-h-26[z];[z]format=yuv420p[out]`;
    ff(['-ss', (m.ss + a).toFixed(2), '-t', t.toFixed(2), '-i', path.join(REC, `${src}.mp4`), '-f', 'lavfi', '-t', '1', '-i', 'color=c=black:s=16x16', ...ov.inputs, '-loop', '1', '-framerate', '30', '-t', len.toFixed(2), '-i', b,
        '-filter_complex', fc, '-map', '[out]', '-an', '-t', len.toFixed(2), ...X264, o]);
    return o;
}
function pieceCard(src, len) {
    const o = out(); ff(['-ss', '0.15', '-t', len.toFixed(2), '-i', path.join(REC, `${src}.mp4`), '-an', '-vf', 'setpts=PTS-STARTPTS,fps=30,format=yuv420p', ...X264, o]); return o;
}
// телефон у рамці зліва + текстова панель справа (16:9): «з телефона» у повному відео
async function piecePhone(src, a, len, speed, panel) {
    const m = meta(src), o = out(); const t = len * speed; zdir++;
    const PW = 416, PH = 900, B = 22, X = 230, Y = 58;
    const fr = await phoneFrame(PW, PH, B), b = await badge(44), mk = await screenMask(PW, PH);
    // права панель — окремий титр на кожну дію (виріб -> опції -> розміри -> підтвердження), послідовно, без накладання
    const sp = spans(m, a, len, speed).filter((x) => x.kind === 'title'); const items = []; let idx = 4;
    for (let i = 0; i < sp.length; i++) {
        const x = sp[i]; const file = await img('pp' + src + i + x.e.text, (f) => png(`<div style="position:absolute;left:860px;top:230px;width:900px">
          <div style="font-size:32px;letter-spacing:.08em;text-transform:uppercase;color:#FE5000;font-weight:700;margin-bottom:18px">${esc(x.e.k)}</div>
          <div style="font-size:62px;font-weight:700;line-height:1.15;color:#fff">${rich(x.e.text)}</div>
          ${i === 0 ? `<div style="font-size:34px;line-height:1.3;color:#BFBFBF;margin-top:34px">${esc(panel.pain)}</div>` : ''}</div>`, 1920, 1080, f));
        if (x.end - x.s < 1.5) WARN.push(`${src}: панель «${x.e.text.slice(0, 30)}» ${(x.end - x.s).toFixed(2)} с < 1,5`);
        items.push({ file, s: x.s, e: x.end, idx: idx++ });
    }
    const ov = overlays('b', items, 1920, 1080);
    const fc = `color=c=0x101820:s=1920x1080:r=30:d=${len.toFixed(2)}[bg];` +
        `[0:v]setpts=(PTS-STARTPTS)/${speed},fps=30,scale=w='${PW}*(${zdir % 2 ? `1+0.045*t/${len.toFixed(2)}` : `1.045-0.045*t/${len.toFixed(2)}`})':h=-2:eval=frame:flags=bicubic,crop=${PW}:${PH}:'(iw-${PW})/2':0,format=rgba[p0];[3:v]format=gray[mk];[p0][mk]alphamerge[ph];` +
        `[bg][ph]overlay=${X + B}:${Y + B}:shortest=1[a];[a][1:v]overlay=${X}:${Y}[b0];` +
        `[b0]drawbox=x=0:y=0:w=1920:h=10:color=0xFE5000:t=fill[b];` + (ov.graph ? ov.graph + ';' : '') +
        `[${ov.last}][2:v]overlay=W-w-34:H-h-26,format=yuv420p`;
    ff(['-ss', (m.ss + a).toFixed(2), '-t', t.toFixed(2), '-i', path.join(REC, `${src}.mp4`), '-i', fr, '-i', b, '-loop', '1', '-framerate', '30', '-t', len.toFixed(2), '-i', mk, ...ov.inputs,
        '-filter_complex', fc, '-an', '-t', len.toFixed(2), ...X264, o]);
    return o;
}
// Reels: телефон 900x1160 (86% ширини кадру) (у безпечній зоні 250..1670), великий титр над ним, плашка ToDo зверху; усередині екрана — повільна «камера»:
// вертикальна прокрутка зображення вгору/вниз (запис масштабовано на повну ширину, видно 1180 із ~1415 px висоти)
async function pieceReel(src, a, len, speed, zm) {
    const m = meta(src), o = out(); const t = len * speed; zdir++;
    const PW = 516, PH = 1116, B = 14, X = (1080 - PW - 2 * B) / 2, Y = 528;
    const fr = await phoneFrame(PW, PH, B), b = await badge(52), bg = await bgReel(), mk = await screenMask(PW, PH);
    const L = len.toFixed(2); const Z = zm ? zm.z : 1, FX = zm ? zm.fx : 0.5, FY = zm ? zm.fy : 0.5;
    // наближення до ключового місця екрана: масштаб 1 -> Z з вибраною точкою фокуса; без наближення запис вписано в рамку точно (нічого не зрізано)
    const ze = Z > 1 ? `(1+${Z - 1}*min(1,t/0.8))` : '1';
    const fc = `[0:v]setpts=(PTS-STARTPTS)/${speed},fps=30,scale=w='${PW}*${ze}':h=-2:eval=frame:flags=bicubic,crop=${PW}:${PH}:'(iw-${PW})*${FX}':'(ih-${PH})*${FY}',format=rgba[p0];[3:v]format=gray[mk];[p0][mk]alphamerge[ph];` +
        `[4:v]format=rgb24[bg];[bg][ph]overlay=${X + B}:${Y + B}:shortest=1[a];[a][1:v]overlay=${X}:${Y}[b];` +
        `[b]drawbox=x=0:y=0:w=1080:h=10:color=0xFE5000:t=fill[c];[c][2:v]overlay=(W-w)/2:262,format=yuv420p`;
    ff(['-ss', (m.ss + a).toFixed(2), '-t', t.toFixed(2), '-i', path.join(REC, `${src}.mp4`), '-i', fr, '-i', b, '-loop', '1', '-framerate', '30', '-t', L, '-i', mk, '-loop', '1', '-framerate', '30', '-t', L, '-i', bg,
        '-filter_complex', fc, '-an', '-t', L, ...X264, o]);
    return o;
}

// ---------------------------------------------------------------- склейка xfade
const TR = ['fade', 'slideleft', 'smoothleft', 'wipeleft', 'fade', 'circleopen', 'slideright', 'smoothright'];
function chain(files, dd, outFile, mixed = true) {
    const durs = files.map(probe); const inp = files.flatMap((f) => ['-i', f]);
    let fc = '', acc = durs[0], last = '[0:v]';
    for (let i = 1; i < files.length; i++) {
        const tr = mixed ? TR[i % TR.length] : 'fade';
        const lab = i === files.length - 1 ? '[v]' : `[x${i}]`;
        fc += `${last}[${i}:v]xfade=transition=${tr}:duration=${dd}:offset=${(acc - dd).toFixed(3)}${lab};`;
        acc += durs[i] - dd; last = lab;
    }
    ff([...inp, '-filter_complex', fc.slice(0, -1), '-map', '[v]', '-c:v', 'libx264', '-crf', '19', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-r', '30', outFile]);
    return acc;
}
function ambient(dur, file) {
    const tone = (f, a) => `${a}*sin(2*PI*${f}*t)`;
    const expr = `(0.55+0.45*sin(2*PI*0.08*t))*(${tone(110, 0.5)}+${tone(164.81, 0.35)}+${tone(220, 0.3)}+${tone(261.63, 0.25)}+${tone(329.63, 0.15)})`;
    ff(['-f', 'lavfi', '-i', `aevalsrc='${expr}':s=44100:d=${dur}`, '-af', `lowpass=f=1800,volume=0.16,afade=t=in:d=1.5,afade=t=out:st=${(dur - 2).toFixed(1)}:d=2`, '-c:a', 'aac', '-b:a', '128k', file]);
}
function finish(silent, target) {
    const dur = probe(silent), aud = out('m4a'); ambient(dur.toFixed(2), aud);
    ff(['-i', silent, '-i', aud, '-c:v', 'copy', '-c:a', 'copy', '-shortest', '-movflags', '+faststart', target]);
    console.log('готово', target, dur.toFixed(1), 'с');
}

const PANEL = {
    M_sale: { k: 'МЕНЕДЖЕР САЛОНУ', pain: 'Замовлення оформлюють на аркушах і в месенджерах, ціну рахують на калькуляторі', gain: 'Розміри, ціна й маржа — просто з телефона' },
    M_prod: { k: 'НАЧАЛЬНИК ВИРОБНИЦТВА', pain: 'Статус замовлень — у чатах і таблицях, вузьке місце видно запізно', gain: 'Дошка замовлень і завантаження дільниць — у кишені' },
    M_store: { k: 'КОМІРНИК', pain: 'Обрізки лежать поза обліком, закупівля не бачить залишків', gain: 'Розмір, площа й резерв обрізка — на екрані телефона' },
    M_margin: { k: 'ВЛАСНИК · ФІНАНСИСТ', pain: 'Маржу замовлення з’ясовують, коли шафа вже виготовлена', gain: 'Маржа кожного замовлення — з телефона, низька — червоним' },
    M_dash: { k: 'ВЛАСНИК · ДИРЕКТОР', pain: 'Щоб побачити фабрику, просять звіти у п’яти людей', gain: 'Вся фабрика — на одному екрані телефона' },
};
// фрагмент запису для Reels = від одного титру до наступного (дія + її підпис), 1,6..3 с, при потребі прискорено
function reelSegs(src, { maxSegs = 9, maxLen = 3.5, skip = 0 } = {}) {
    const m = meta(src); const ev = (m.events || []).filter((e) => e.type === 'title').sort((x, y) => x.t - y.t); const res = [];
    ev.forEach((e, i) => {
        const nxt = ev[i + 1]; const endT = Math.min(nxt ? nxt.t : m.ss + m.dur, e.t + 7.5); const L = endT - e.t; if (L < 1.3) return;
        const speed = Math.min(2.6, Math.max(1, L / maxLen)); res.push({ src, a: Math.max(0, e.t - m.ss), len: L / speed, speed, ttl: { k: e.k, short: e.short } });
    });
    return res.slice(skip, skip + maxSegs);
}

const REEL_OPT = {};
// наближення в Reels (1,6–2×) до ключового місця екрана: ключ — «шматок титру»; z — масштаб, fx/fy — точка фокуса 0..1 (праворуч/вниз)
const ZOOM = {
    'M_sale|Обираємо **декор** — ціна змінюється': { z: 1.5, fx: 0.8, fy: 1 }, 'M_sale|Вводимо **розміри**': { z: 1.5, fx: 0.8, fy: 1 },
    'M_sale|Ціна й **маржа — ще в пропозиції**': { z: 1.7, fx: 0.5, fy: 0.95 }, 'M_prod|**Понад 100 %** — вузьке місце видно до зриву': { z: 1.6, fx: 0.5, fy: 0.25 },
    'M_dash|**Низьку маржу** видно одразу': { z: 1.8, fx: 0.1, fy: 0.12 }, 'M_dash|Де **понад 100 %** — вузьке місце': { z: 1.6, fx: 0.5, fy: 0.3 },
    'M_store|Наступний розкрій **бере їх першими**': { z: 1.6, fx: 0.3, fy: 0.15 }, 'M_margin|Нижче 15 % — **червоним**': { z: 1.7, fx: 0.9, fy: 0.1 },
};
const zoomFor = (src, short) => ZOOM[src + '|' + short] || null;
const which = process.argv[2] || 'all';
browser = await chromium.launch();
if (which === 'full' || which === 'all') {
    const P = [];
    P.push(pieceCard('F_intro', 7.4));
    P.push(await pieceDesk('D_dash', 0, meta('D_dash').dur));
    P.push(await pieceDesk('D_sale', 0, meta('D_sale').dur / 1.2, 1.2));
    P.push(await pieceDesk('D_board', 0, meta('D_board').dur));
    P.push(await pieceDesk('D_prod', 0, meta('D_prod').dur / 1.1, 1.1));
    P.push(await pieceDesk('D_cut', 0, meta('D_cut').dur));
    P.push(await pieceDesk('D_store', 0, meta('D_store').dur));
    P.push(await pieceDesk('D_margin', 0, meta('D_margin').dur));
    for (const n of ['M_sale', 'M_prod', 'M_store', 'M_margin', 'M_dash']) P.push(await piecePhone(n, 0, meta(n).dur / (n === 'M_sale' ? 1.0 : 1.15), n === 'M_sale' ? 1.0 : 1.15, PANEL[n]));
    P.push(pieceCard('F_outro', 7.6));
    const sil = path.join(tmp, 'full_silent.mp4'); chain(P, 0.5, sil);
    finish(sil, path.join(ROOT, 'video', 'mebli-full-16x9.mp4'));
}
if (which === 'reels' || which === 'all') {
    const P = [], T = []; // T[i] — титр шматка i (або null); титри накладаються ПІСЛЯ склейки, між шматками гаснуть, нове — після старого
    P.push(pieceCard('R_hook', 3.3)); T.push(null);
    for (const n of ['M_sale', 'M_prod', 'M_store', 'M_margin', 'M_dash']) {
        const segs = reelSegs(n, REEL_OPT[n] || {});
        for (let i = 0; i < segs.length; i++) { const s = segs[i]; P.push(await pieceReel(s.src, s.a, s.len, s.speed, zoomFor(n, s.ttl.short))); T.push(s.ttl); }
    }
    P.push(pieceCard('R_outro', 6.3)); T.push(null);
    const sil0 = path.join(tmp, 'reels_silent0.mp4'); const dur = chain(P, 0.25, sil0);
    const durs = P.map(probe); const items = []; let off = 0, idx = 1;
    for (let i = 0; i < P.length; i++) {
        if (T[i]) { const s = off + 0.28, e = off + durs[i] - 0.1; if (e - s < 1.5) WARN.push(`Reels: титр «${T[i].short.slice(0, 30)}» ${(e - s).toFixed(2)} с < 1,5`); items.push({ file: await titleReel(T[i].k, T[i].short), s, e, idx: idx++, x: 0, y: 0 }); }
        off += durs[i] - 0.25;
    }
    const ov = overlays('a', items, 1080, 1920); const sil = path.join(tmp, 'reels_silent.mp4');
    ff(['-i', sil0, ...ov.inputs, '-filter_complex', `[0:v]null[a];${ov.graph};[${ov.last}]format=yuv420p[out]`, '-map', '[out]', '-an', ...X264, sil]);
    console.log('Reels шматків:', P.length, 'тривалість', dur.toFixed(1));
    finish(sil, path.join(ROOT, 'video', 'mebli-reels-9x16.mp4'));
}
if (WARN.length) console.log('ПОПЕРЕДЖЕННЯ:\n' + WARN.join('\n'));
await browser.close();
fs.rmSync(tmp, { recursive: true, force: true });
