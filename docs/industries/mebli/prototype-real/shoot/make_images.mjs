// Генератор вигаданих зображень демо-фабрики (логотип, аватари, вироби): SVG -> PNG через chromium.
// Усе намальовано тут, чужих фото й торгових марок немає. Запуск: node make_images.mjs
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const here = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(here, '../../../../../package/addons/td_mebli_demo/static/img');

const wrap = (size, body, defs = '') =>
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${size} ${size}" width="${size}" height="${size}"><defs>${defs}</defs>${body}</svg>`;

// ---- логотип: шафа з розсувними дверима в рамці
const logo = wrap(512, `<rect width="512" height="512" rx="96" fill="#3d2b1f"/>
<rect x="116" y="92" width="280" height="316" rx="10" fill="none" stroke="#e8c99a" stroke-width="22"/>
<path d="M256 92v316" stroke="#e8c99a" stroke-width="22"/>
<rect x="206" y="226" width="14" height="70" rx="7" fill="#e8c99a"/><rect x="292" y="226" width="14" height="70" rx="7" fill="#e8c99a"/>
<rect x="136" y="420" width="44" height="30" fill="#e8c99a"/><rect x="332" y="420" width="44" height="30" fill="#e8c99a"/>`);

// ---- аватари (вигадані люди): різні обличчя, зачіски, одяг, деталі професії
const face = (o) => {
    const { bg, skin, hair, shirt, hairStyle, extra = '', cheek = '#e9a38c' } = o;
    const hairBack = hairStyle === 'long' ? `<path d="M70 120c0-62 40-86 58-86s58 24 58 86v92c-14 14-30 18-58 18s-44-4-58-18z" fill="${hair}"/>` : '';
    const hairTop = {
        long: `<path d="M84 104c4-40 28-58 44-58s40 18 44 58c-18-14-34-20-44-20s-26 6-44 20z" fill="${hair}"/>`,
        short: `<path d="M82 104c0-34 20-54 46-54s46 20 46 54c-10-12-24-20-46-20s-36 8-46 20z" fill="${hair}"/>`,
        bald: `<path d="M86 96c8-20 24-28 42-28s34 8 42 28c-12-8-26-12-42-12s-30 4-42 12z" fill="${hair}" opacity=".55"/>`,
        curly: `<g fill="${hair}"><circle cx="92" cy="92" r="20"/><circle cx="118" cy="76" r="22"/><circle cx="148" cy="76" r="22"/><circle cx="170" cy="94" r="20"/><circle cx="104" cy="106" r="14"/><circle cx="156" cy="106" r="14"/></g>`,
        grey: `<path d="M82 104c0-34 20-52 46-52s46 18 46 52c-10-10-24-18-46-18s-36 8-46 18z" fill="${hair}"/>`,
    }[hairStyle];
    return wrap(256, `<rect width="256" height="256" fill="${bg}"/>
${hairBack}
<path d="M28 256c0-62 42-92 100-92s100 30 100 92z" fill="${shirt}"/>
<path d="M104 164l24 34 24-34z" fill="#fff" opacity=".85"/>
<rect x="112" y="136" width="32" height="34" rx="12" fill="${skin}"/>
<ellipse cx="128" cy="108" rx="44" ry="50" fill="${skin}"/>
<ellipse cx="104" cy="122" rx="8" ry="5" fill="${cheek}" opacity=".5"/><ellipse cx="152" cy="122" rx="8" ry="5" fill="${cheek}" opacity=".5"/>
<circle cx="112" cy="106" r="4.5" fill="#2b2118"/><circle cx="144" cy="106" r="4.5" fill="#2b2118"/>
<path d="M114 128q14 12 28 0" stroke="#7a3d2e" stroke-width="4" fill="none" stroke-linecap="round"/>
${hairTop}${extra}`);
};
const avatars = {
    salon: face({ bg: '#f6dfd0', skin: '#f1c9a8', hair: '#6a3b1f', shirt: '#b5523b', hairStyle: 'long' }),
    salon2: face({ bg: '#e9efe0', skin: '#e3b894', hair: '#2b2b2b', shirt: '#7a8a3a', hairStyle: 'short',
        extra: '<path d="M104 170h48l-8 14h-32z" fill="#e8e0b8"/>' }),
    salon3: face({ bg: '#f4e1ea', skin: '#f6d6bd', hair: '#b9772e', shirt: '#9a4a78', hairStyle: 'long', cheek: '#f09aa0' }),
    tech: face({ bg: '#dde8f0', skin: '#e8bf9a', hair: '#2f2a28', shirt: '#2f5d7c', hairStyle: 'short',
        extra: '<g fill="none" stroke="#2b2118" stroke-width="4"><rect x="96" y="96" width="26" height="20" rx="6"/><rect x="134" y="96" width="26" height="20" rx="6"/><path d="M122 104h12"/></g>' }),
    chief: face({ bg: '#f1e6c6', skin: '#d9a77f', hair: '#4a4a4a', shirt: '#d98a1f', hairStyle: 'grey',
        extra: '<path d="M80 86c0-30 22-46 48-46s48 16 48 46z" fill="#f4c542"/><rect x="72" y="84" width="112" height="12" rx="6" fill="#e1a91b"/>' }),
    store: face({ bg: '#e1efdc', skin: '#f3d0b0', hair: '#a4552c', shirt: '#4f8a4a', hairStyle: 'curly',
        extra: '<path d="M96 170h64v86H96z" fill="#3f7a3a" opacity=".55"/>' }),
    fin: face({ bg: '#e6e1f0', skin: '#c58d66', hair: '#1f1a18', shirt: '#4b3f72', hairStyle: 'short',
        extra: '<path d="M122 170h12l6 56-12 10-12-10z" fill="#c9a06a"/>' }),
};

// ---- вироби
const wood = (id, a, b) => `<linearGradient id="${id}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="${a}"/><stop offset="1" stop-color="${b}"/></linearGradient>`;
const floor = '<rect width="1024" height="1024" fill="#f4efe8"/><rect y="800" width="1024" height="224" fill="#e7dfd3"/><ellipse cx="512" cy="880" rx="400" ry="34" fill="#00000018"/>';
const grain = (x, y, w, h, n) => `<g stroke="#9a7447" stroke-width="2" opacity=".35">${Array.from({ length: n }, (_, i) => `<path d="M${x + (i + 1) * w / (n + 1)} ${y + 8}v${h - 16}"/>`).join('')}</g>`;

const wardrobe = wrap(1024, `${floor}
<rect x="232" y="110" width="560" height="760" rx="6" fill="#a97b4b"/>
<rect x="246" y="124" width="266" height="732" fill="url(#w1)"/><rect x="512" y="124" width="266" height="732" fill="url(#w2)"/>
${grain(246, 124, 266, 732, 7)}${grain(512, 124, 266, 732, 7)}
<rect x="246" y="124" width="266" height="732" fill="none" stroke="#8a6338" stroke-width="3"/><rect x="512" y="124" width="266" height="732" fill="none" stroke="#8a6338" stroke-width="3"/>
<rect x="486" y="430" width="10" height="190" rx="5" fill="#5e4a30"/><rect x="528" y="430" width="10" height="190" rx="5" fill="#5e4a30"/>
<rect x="246" y="112" width="532" height="12" fill="#6e5230"/><rect x="246" y="856" width="532" height="12" fill="#6e5230"/>
<rect x="262" y="868" width="44" height="22" fill="#3f3120"/><rect x="718" y="868" width="44" height="22" fill="#3f3120"/>
<rect x="246" y="124" width="266" height="44" fill="#fff" opacity=".1"/>`, wood('w1', '#dcbd92', '#cfae82') + wood('w2', '#cba679', '#bf986c'));

const dresser = wrap(1024, `${floor}
<rect x="222" y="300" width="580" height="500" rx="8" fill="#e8e4dd" stroke="#c9c2b6" stroke-width="3"/>
${[0, 1, 2, 3].map((i) => `<rect x="244" y="${322 + i * 116}" width="536" height="104" rx="4" fill="#f9f7f3" stroke="#cdc6ba" stroke-width="3"/>
<rect x="452" y="${362 + i * 116}" width="120" height="14" rx="7" fill="#8d8575"/>`).join('')}
<rect x="200" y="286" width="624" height="22" rx="6" fill="#d8d2c6" stroke="#b9b1a2" stroke-width="3"/>
<rect x="250" y="800" width="26" height="46" fill="#5a5247"/><rect x="748" y="800" width="26" height="46" fill="#5a5247"/>`);

const kitchen = wrap(1024, `<rect width="1024" height="1024" fill="#f1ebe2"/><rect y="760" width="1024" height="264" fill="#e3dacd"/>
<rect x="90" y="150" width="844" height="220" rx="6" fill="#3b3f44"/>
${[0, 1, 2].map((i) => `<rect x="${104 + i * 276}" y="164" width="262" height="192" rx="4" fill="#4a4f55"/><rect x="${104 + i * 276 + 90}" y="${i === 1 ? 300 : 300}" width="82" height="12" rx="6" fill="#c9a06a"/>`).join('')}
<rect x="70" y="520" width="884" height="26" rx="6" fill="#c9c2b6"/>
${[0, 1, 2].map((i) => `<rect x="${96 + i * 282}" y="548" width="268" height="${i === 1 ? 190 : 210}" rx="4" fill="#d8bb91" stroke="#a97b4b" stroke-width="3"/>
<rect x="${96 + i * 282 + 90}" y="568" width="88" height="12" rx="6" fill="#5e4a30"/>`).join('')}
<rect x="378" y="548" width="268" height="190" fill="#3b3f44" opacity="0"/>
<rect x="400" y="500" width="224" height="20" rx="8" fill="#9aa4ad"/>
<rect x="96" y="758" width="40" height="22" fill="#4a3a26"/><rect x="890" y="758" width="40" height="22" fill="#4a3a26"/>`);

const write = (name, svg) => fs.writeFileSync(path.join(OUT, name + '.svg'), svg);
write('logo', logo);
for (const [k, v] of Object.entries(avatars)) write('avatar_' + k, v);
write('prod_wardrobe', wardrobe); write('prod_dresser', dresser); write('prod_kitchen', kitchen);

const browser = await chromium.launch();
const page = await browser.newPage();
for (const f of fs.readdirSync(OUT).filter((x) => x.endsWith('.svg'))) {
    const svg = fs.readFileSync(path.join(OUT, f), 'utf8');
    const size = parseInt(/width="(\d+)"/.exec(svg)[1], 10);
    await page.setViewportSize({ width: size, height: size });
    await page.setContent(`<body style="margin:0;background:transparent">${svg}</body>`);
    await page.screenshot({ path: path.join(OUT, f.replace('.svg', '.png')), omitBackground: true });
    console.log('png', f);
}
await browser.close();
