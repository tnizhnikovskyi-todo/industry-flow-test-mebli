// Монтаж двох відео з живих записів (video/rec/*.mp4): короткі фрагменти, плавні переходи ffmpeg xfade, ambient-звук (AAC).
// Використання: node montage.mjs [full|reels|all]. Плашки/титри/курсор уже в записі; тут — обрізання, прискорення, наближення (crop), рамка
// телефона, текстова панель біля телефона (drawtext, Open Sans), логотип ToDo, фон #101820.
import fs from 'fs'; import os from 'os'; import path from 'path';
import { execFileSync } from 'child_process';
import { createRequire } from 'module';
import { fileURLToPath, pathToFileURL } from 'url';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const here = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(here, '..');
const REC = path.join(ROOT, 'video', 'rec');
const FONT = path.join(ROOT, 'brand-todo/fonts/OpenSans-bold.ttf');
const FONT_R = path.join(ROOT, 'brand-todo/fonts/OpenSans-regular.ttf');
const LOGO = path.join(ROOT, 'brand-todo/todo-logo.png');
const tmp = fs.mkdtempSync(path.join(process.env.TMPDIR || os.tmpdir(), 'mebli-mont-'));
const ff = (args) => execFileSync('ffmpeg', ['-v', 'error', '-y', ...args], { stdio: ['ignore', 'inherit', 'inherit'] });
const probe = (f) => parseFloat(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).toString());
const meta = (n) => JSON.parse(fs.readFileSync(path.join(REC, `${n}.json`), 'utf8'));
let seq = 0; const out = (ext = 'mp4') => path.join(tmp, `p${String(seq++).padStart(3, '0')}.${ext}`);
const wrap = (s, n) => { const w = s.split(' '); const L = []; let cur = ''; for (const x of w) { if ((cur + ' ' + x).trim().length > n) { L.push(cur.trim()); cur = x; } else cur = cur + ' ' + x; } L.push(cur.trim()); return L.join('\n'); };
const txt = (s) => { const f = out('txt'); fs.writeFileSync(f, s); return f.replace(/\\/g, '/').replace(/:/g, '\\:'); };

// ---------- рамка телефона (нейтральна, CSS) із прозорим «екраном»
async function phoneFrame(w, h, b, file) {
    const br = await chromium.launch(); const pg = await br.newPage({ viewport: { width: w + 2 * b, height: h + 2 * b } });
    await pg.setContent(`<body style="margin:0;background:transparent"><div style="width:${w + 2 * b}px;height:${h + 2 * b}px;box-sizing:border-box;border:${b}px solid #0b0f14;border-radius:${Math.round(w * .13)}px;box-shadow:inset 0 0 0 3px #2a333d"></div>
      <div style="position:absolute;left:50%;top:${Math.round(b * .35)}px;width:${Math.round(w * .24)}px;height:${Math.round(b * .3)}px;margin-left:-${Math.round(w * .12)}px;background:#1b232c;border-radius:99px"></div></body>`);
    await pg.screenshot({ path: file, omitBackground: true }); await br.close();
}

// ---------- шматок запису: [a,b] від початку «живої» частини, швидкість, наближення (z: {s,x,y}, x/y 0..1 — прив'язка кропу)
function cropExpr(z) { if (!z) return ''; return `crop=iw/${z.s}:ih/${z.s}:(iw-iw/${z.s})*${z.x ?? 0}:(ih-ih/${z.s})*${z.y ?? 0},`; }

// повільний «камерний» рух (push-in / pull-out) на всіх шматках: жодного нерухомого кадру довше за ~1,5 с, навіть коли в Odoo пауза
let zdir = 0;
function zp(T, W, H, amp = 0.07) {
    zdir++; const n = Math.max(1, Math.round(T * 30)); const e = zdir % 2 ? `1+${amp}*on/${n}` : `${1 + amp}-${amp}*on/${n}`;
    return `scale=${W * 1.5}:${H * 1.5}:flags=bicubic,zoompan=z='${e}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=${W}x${H}:fps=30`;
}
// desktop: повний кадр 1920x1080
function pieceDesk(src, a, len, speed = 1, z = null) {
    const m = meta(src), o = out(); const t = len * speed;
    ff(['-ss', (m.ss + a).toFixed(2), '-t', t.toFixed(2), '-i', path.join(REC, `${src}.mp4`), '-an', '-vf',
        `setpts=(PTS-STARTPTS)/${speed},${cropExpr(z)}fps=30,${zp(len, 1920, 1080)},format=yuv420p`, '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', o]);
    return o;
}
function pieceCard(src, len) { // заставка: беремо з початку без обрізання меж, повного розміру
    const o = out(); const dims = src.startsWith('R_') ? '1080:1920' : '1920:1080';
    ff(['-ss', '0.15', '-t', len.toFixed(2), '-i', path.join(REC, `${src}.mp4`), '-an', '-vf', `setpts=PTS-STARTPTS,fps=30,${zp(len, ...dims.split(':').map(Number), 0.05)},format=yuv420p`, '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', o]);
    return o;
}
// телефон у рамці зліва + текстова панель справа (16:9)
function piecePhone(src, a, len, speed, z, panel) {
    const m = meta(src), o = out(); const t = len * speed;
    const PW = 548, PH = 898, B = 22, X = 150, Y = 60;
    const k = txt(panel.k), p = txt(wrap(panel.pain, 27)), g = txt(wrap(panel.gain, 24));
    const fc = `color=c=0x101820:s=1920x1080:r=30:d=${len.toFixed(2)}[bg];` +
        `[0:v]setpts=(PTS-STARTPTS)/${speed},${cropExpr(z)}fps=30,${zp(len, PW, PH, 0.06)}[ph];` +
        `[bg][ph]overlay=${X + B}:${Y + B}:shortest=1[a];[a][1:v]overlay=${X}:${Y}[b];` +
        `[b]drawbox=x=0:y=0:w=1920:h=10:color=0xFE5000:t=fill,` +
        `drawtext=fontfile='${FONT}':textfile='${k}':x=860:y=250:fontsize=34:fontcolor=0xFE5000:alpha='min(1,t/0.5)',` +
        `drawtext=fontfile='${FONT_R}':textfile='${p}':x=860:y=310:fontsize=38:fontcolor=0xBFBFBF:line_spacing=10:alpha='min(1,max(0,(t-0.3)/0.5))',` +
        `drawtext=fontfile='${FONT}':textfile='${g}':x=860:y=560:fontsize=62:fontcolor=white:line_spacing=14:alpha='min(1,max(0,(t-0.9)/0.5))'[c];` +
        `[2:v]scale=-1:60[lg];[c]drawbox=x=1650:y=34:w=240:h=80:color=white:t=fill[d];[d][lg]overlay=1672:44,format=yuv420p`;
    ff(['-ss', (m.ss + a).toFixed(2), '-t', t.toFixed(2), '-i', path.join(REC, `${src}.mp4`), '-i', path.join(tmp, 'frame_full.png'), '-i', LOGO,
        '-filter_complex', fc, '-an', '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-t', len.toFixed(2), o]);
    return o;
}
// Reels: телефонний запис на всю ширину (820x1346) у безпечній зоні 250..1670, логотип ToDo над ним
function pieceReel(src, a, len, speed, z) {
    const m = meta(src), o = out(); const t = len * speed;
    const fc = `color=c=0x101820:s=1080x1920:r=30:d=${len.toFixed(2)}[bg];` +
        `[0:v]setpts=(PTS-STARTPTS)/${speed},${cropExpr(z)}fps=30,${zp(len, 820, 1346, 0.06)}[ph];` +
        `[bg][ph]overlay=130:310:shortest=1[a];[a]drawbox=x=124:y=304:w=832:h=1358:color=0xFE5000:t=6[b];` +
        `[b]drawbox=x=0:y=0:w=1080:h=10:color=0xFE5000:t=fill[c];[1:v]scale=-1:44[lg];[c]drawbox=x=410:y=250:w=260:h=48:color=white:t=fill[d];[d][lg]overlay=424:252,format=yuv420p`;
    ff(['-ss', (m.ss + a).toFixed(2), '-t', t.toFixed(2), '-i', path.join(REC, `${src}.mp4`), '-i', LOGO,
        '-filter_complex', fc, '-an', '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-t', len.toFixed(2), o]);
    return o;
}

// ---------- склейка xfade
const TR = ['fade', 'slideleft', 'smoothleft', 'wipeleft', 'fade', 'circleopen', 'slideright', 'smoothright'];
function chain(files, d, outFile, trs = TR) {
    const durs = files.map(probe); const inp = files.flatMap((f) => ['-i', f]);
    let fc = '', acc = durs[0], last = '[0:v]';
    for (let i = 1; i < files.length; i++) {
        const tr = Array.isArray(d) ? trs[i % trs.length] : 'fade', dd = Array.isArray(d) ? d[0] : d;
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
// розбиття запису на шматки по ~step секунд (змінюємо план) з чергуванням наближень
function splitPieces(src, speed, step, mk, zooms) {
    const D = meta(src).dur; const n = Math.max(1, Math.round(D / speed / step)); const L = D / n; const res = [];
    for (let i = 0; i < n; i++) res.push(mk(src, i * L, L / speed, speed, zooms[i % zooms.length]));
    return res;
}

const which = process.argv[2] || 'all';
const PANEL = {
    M_sale: { k: 'МЕНЕДЖЕР САЛОНУ', pain: 'Замовлення оформлюють на аркушах і в месенджерах, ціну рахують на калькуляторі', gain: 'Розміри, ціна й маржа — просто з телефона' },
    M_prod: { k: 'НАЧАЛЬНИК ВИРОБНИЦТВА', pain: 'Статус замовлень — у чатах і таблицях, вузьке місце видно запізно', gain: 'Дошка замовлень і завантаження дільниць — у кишені' },
    M_store: { k: 'КОМІРНИК', pain: 'Обрізки лежать поза обліком, закупівля не бачить залишків', gain: 'Розмір, площа й резерв обрізка — на екрані телефона' },
    M_margin: { k: 'ВЛАСНИК · ФІНАНСИСТ', pain: 'Маржу замовлення з’ясовують, коли шафа вже виготовлена', gain: 'Маржа кожного замовлення — з телефона, низька — червоним' },
    M_dash: { k: 'ВЛАСНИК · ДИРЕКТОР', pain: 'Щоб побачити фабрику, просять звіти у п’яти людей', gain: 'Вся фабрика — на одному екрані телефона' },
};

if (which === 'full' || which === 'all') {
    await phoneFrame(548, 898, 22, path.join(tmp, 'frame_full.png'));
    const P = [];
    P.push(pieceCard('F_intro', 7.4));
    P.push(pieceDesk('D_dash', 0, meta('D_dash').dur));
    P.push(pieceDesk('D_sale', 0, meta('D_sale').dur / 1.25, 1.25));
    P.push(pieceDesk('D_prod', 0, meta('D_prod').dur / 1.1, 1.1));
    P.push(pieceDesk('D_cut', 0, meta('D_cut').dur));
    P.push(pieceDesk('D_store', 0, meta('D_store').dur));
    P.push(pieceDesk('D_margin', 0, meta('D_margin').dur));
    for (const n of ['M_sale', 'M_prod', 'M_store', 'M_margin', 'M_dash']) P.push(piecePhone(n, 0, meta(n).dur, 1, null, PANEL[n]));
    P.push(pieceCard('F_outro', 7.6));
    const sil = path.join(tmp, 'full_silent.mp4'); chain(P, [0.5], sil);
    finish(sil, path.join(ROOT, 'video', 'mebli-full-16x9.mp4'));
}
if (which === 'reels' || which === 'all') {
    const P = [];
    const Z = [null, { s: 1.25, x: 0, y: 1 }, null, { s: 1.3, x: 1, y: 1 }];
    P.push(pieceCard('R_hook', 3.2));
    P.push(...splitPieces('M_sale', 1.2, 2.8, pieceReel, Z));
    P.push(...splitPieces('M_prod', 1.15, 2.8, pieceReel, Z));
    P.push(...splitPieces('M_store', 1.1, 2.8, pieceReel, Z));
    P.push(...splitPieces('M_margin', 1.1, 2.8, pieceReel, Z));
    P.push(...splitPieces('M_dash', 1.0, 3.0, pieceReel, [null, { s: 1.18, x: 0, y: 1 }]));
    P.push(pieceCard('R_outro', 6.2));
    const sil = path.join(tmp, 'reels_silent.mp4'); const dur = chain(P, [0.25], sil);
    console.log('Reels шматків:', P.length, 'тривалість', dur.toFixed(1));
    finish(sil, path.join(ROOT, 'video', 'mebli-reels-9x16.mp4'));
}
fs.rmSync(tmp, { recursive: true, force: true });
