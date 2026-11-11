// Анімовані заставки ToDo (HTML+CSS-анімація, записані так само, як Odoo): початок і кінець відео, гачок Reels. Стиль — brand-todo/BRAND.md.
import fs from 'fs'; import path from 'path'; import { pathToFileURL } from 'url';
import { launch, clip, sleep, ROOT } from './rec_lib.mjs';
const here = path.dirname(new URL(import.meta.url).pathname);
const LOGO = pathToFileURL(path.join(ROOT, 'brand-todo/todo-logo.png')).href;
const CSS = pathToFileURL(path.join(here, 'brand.css')).href;
const FULL = { viewport: { width: 1600, height: 900 }, rec: { width: 1920, height: 1080 } };
const REEL = { viewport: { width: 900, height: 1600 }, rec: { width: 1080, height: 1920 } };
const page = (body, extra = '') => `<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="${CSS}"><style>
html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#101820}
.bg{position:absolute;inset:0;background:radial-gradient(60% 50% at var(--gx,20%) var(--gy,30%),rgba(254,80,0,.28),transparent 70%);animation:glow 8s ease-in-out infinite alternate}
@keyframes glow{to{--gx:80%;--gy:70%;transform:scale(1.15) rotate(3deg)}}
.bar{position:absolute;left:0;top:0;height:10px;background:#FE5000;animation:bar 7s ease-out forwards}@keyframes bar{from{width:0}to{width:100%}}
.stage{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;color:#fff;font-family:'Open Sans',sans-serif;padding:0 70px}
.in{opacity:0;transform:translateY(46px) scale(.97);animation:in .7s cubic-bezier(.2,.8,.2,1) forwards;animation-delay:var(--d,0s)}
.out{opacity:0;transform:translateY(46px);animation:in .7s cubic-bezier(.2,.8,.2,1) forwards var(--d,0s), out .6s ease-in forwards var(--o,3s)}
@keyframes in{to{opacity:1;transform:none}}@keyframes out{to{opacity:0;transform:translateY(-30px)}}
em{font-style:normal;color:#FE5000}.drift{animation:drift 10s linear forwards}@keyframes drift{from{transform:scale(1)}to{transform:scale(1.06)}}
${extra}</style></head><body><div class="bg"></div><div class="bar"></div>${body}</body></html>`;
const write = (n, html) => { const f = path.join(here, `_card_${n}.html`); fs.writeFileSync(f, html); return pathToFileURL(f).href; };
const logo = (h, d) => `<img class="in" style="--d:${d}s;height:${h}px;background:#fff;border-radius:24px;padding:${h * .2}px ${h * .34}px;margin-bottom:46px" src="${LOGO}">`;

const CARDS = {
    F_intro: [FULL, 7.4, `<div class="stage drift">
        <div class="out" style="--d:.2s;--o:3.9s;font-size:76px;font-weight:700;line-height:1.2">Замовлення — <em>в Excel і месенджерах</em></div>
        <div class="out" style="--d:1.2s;--o:3.9s;font-size:76px;font-weight:700;line-height:1.2;margin-top:18px">Обрізки — <em>на смітник</em></div>
        <div class="out" style="--d:2.2s;--o:3.9s;font-size:76px;font-weight:700;line-height:1.2;margin-top:18px">Маржу бачите — <em>через місяць</em></div>
        <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 70px">
        ${logo(130, 4.6)}<div class="in" style="--d:5s;font-size:52px;font-weight:700;line-height:1.25">ToDo показує, як меблеву фабрику<br>веде <em>Odoo 19</em></div>
        <div class="in" style="--d:5.7s;font-size:26px;color:#BFBFBF;margin-top:26px">Меблева фабрика «Демо» · вигадані дані</div></div></div>`],
    F_outro: [FULL, 8, `<div class="stage">${logo(150, 0.1)}
        <div class="in" style="--d:.6s;font-size:66px;font-weight:700;line-height:1.15">ToDo — впровадження Odoo<br>для виробництв</div>
        <div class="in" style="--d:1.3s;margin-top:44px;background:#FE5000;color:#fff;font-weight:700;font-size:56px;padding:16px 56px;border-radius:999px">todo.ltd</div>
        <div class="in" style="--d:1.9s;font-size:40px;margin-top:34px">Покажемо на <em>ваших даних</em></div>
        <div class="in" style="--d:2.6s;font-size:22px;color:#808080;margin-top:34px;max-width:1400px">Показ на вигаданих даних · Odoo 19 + модулі пакета «меблі» · розкрій — імітація програми розкрою</div></div>`],
    R_hook: [REEL, 3.3, `<div class="stage" style="padding:250px 56px">
        <div style="font-size:30px;letter-spacing:.08em;text-transform:uppercase;color:#FE5000;font-weight:700;margin-bottom:26px">Власнику меблевої фабрики</div>
        <div style="font-size:78px;font-weight:700;line-height:1.16">Скільки ви втрачаєте, коли <span class="hl" style="--d:.4s">маржу</span> бачите вже <span class="hl" style="--d:1.2s">після відвантаження?</span></div>
        <div style="font-size:36px;color:#BFBFBF;margin-top:34px">Покажемо, як це виглядає в Odoo ↓</div></div>`,
        `.hl{color:#fff;animation:hl .35s ease-out forwards var(--d,0s)}@keyframes hl{to{color:#FE5000}}`],
    R_outro: [REEL, 6.5, `<div class="stage" style="padding:250px 56px">${logo(120, 0.1)}
        <div class="in" style="--d:.5s;font-size:66px;font-weight:700;line-height:1.15">ToDo — впровадження Odoo для виробництв</div>
        <div class="in" style="--d:1.1s;margin-top:44px;background:#FE5000;color:#fff;font-weight:700;font-size:62px;padding:14px 54px;border-radius:999px">todo.ltd</div>
        <div class="in" style="--d:1.7s;font-size:44px;margin-top:36px;font-weight:700">Покажемо на <em>ваших даних</em></div>
        <div class="in" style="--d:2.4s;font-size:30px;color:#BFBFBF;margin-top:40px">Показ на вигаданих даних · розкрій — імітація</div></div>`],
};
await launch();
for (const n of process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(CARDS)) {
    const [dev, secs, body, extra] = CARDS[n]; const url = write(n, page(body, extra || ''));
    await clip(n, { plain: true, url, dev }, async (c) => { await sleep(300); c.mark(); await sleep(secs * 1000); });
}
process.exit(0);
