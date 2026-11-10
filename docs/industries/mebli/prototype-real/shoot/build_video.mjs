// Збірка відео зі сцен (scenes.mjs + ffmpeg). Використання: node build_video.mjs [full|reels|all]
// Виходи: video/mebli-full-16x9.mp4 (1920x1080) і video/mebli-reels-9x16.mp4 (1080x1920), H.264, 30 fps, AAC (тиха фонова доріжка).
// Рух у кадрі: прокрутка (crop) і наближення до ключової цифри (zoompan) на скриншотах Odoo; заставки й титри — HTML сцени.
import fs from 'fs'; import path from 'path'; import os from 'os';
import { execFileSync } from 'child_process';
import { ROOT, SIZE, WIN, PHONE_WIN, renderScenes } from './scenes.mjs';
import { full, reels } from './video_spec.mjs';

const which = process.argv[2] || 'all';
const TARGETS = { full: { fmt: 'full', spec: full, out: 'mebli-full-16x9.mp4' }, reels: { fmt: 'reels', spec: reels, out: 'mebli-reels-9x16.mp4' } };
const FPS = 30, FADE = 0.25;
const ff = (args) => execFileSync('ffmpeg', ['-y', '-loglevel', 'error', ...args], { maxBuffer: 1 << 26 });
const probe = (file, entry) => execFileSync('ffprobe', ['-v', 'error', '-show_entries', entry, '-of', 'csv=p=0', file]).toString().trim();

function clipStatic(png, d, out) {
    ff(['-loop', '1', '-framerate', String(FPS), '-t', String(d), '-i', png,
        '-vf', `fade=t=in:st=0:d=${FADE},fade=t=out:st=${(d - FADE).toFixed(2)}:d=${FADE},format=yuv420p`,
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-r', String(FPS), '-pix_fmt', 'yuv420p', out]);
}

// рухоме вікно: shot (десктоп 16:9 або телефон у Reels) і shotphone (телефон у 16:9)
function clipShot(fmt, sc, overlayPng, d, out) {
    const { w, h } = SIZE[fmt];
    const win = sc.win || (sc.type === 'shotphone' ? PHONE_WIN : WIN[fmt]);
    const src = path.join(ROOT, sc.img);
    const [sw, sh] = probe(src, 'stream=width,height').split(',').map(Number);
    const cropBottom = sc.cropBottom ?? 0;
    const scaledH = Math.round(((sh - cropBottom) * win.w) / sw);
    if (scaledH < win.h) throw new Error(`скриншот ${sc.img} надто низький для вікна: ${scaledH} < ${win.h}`);
    const [p0, p1] = sc.pan || [0, 0];
    const z = sc.zoom || { z: 1, fx: 0.5, fy: 0.5 };
    const frames = Math.round(d * FPS);
    const sup = 2; // суперсемплінг перед zoompan: без тремтіння
    const zoom = z.z > 1
        ? `scale=${win.w * sup}:${win.h * sup}:flags=lanczos,zoompan=z='1+${(z.z - 1).toFixed(3)}*on/${frames}':x='(iw-iw/zoom)*${z.fx}':y='(ih-ih/zoom)*${z.fy}':d=1:s=${win.w}x${win.h}:fps=${FPS},`
        : '';
    const filter = `[1:v]crop=iw:ih-${cropBottom}:0:0,scale=${win.w}:-2:flags=lanczos,` +
        `crop=${win.w}:${win.h}:0:'(ih-${win.h})*(${p0}+(${p1}-${p0})*t/${d})',${zoom}setsar=1[win];` +
        `[0:v][win]overlay=${win.x}:${win.y}[a];[a][2:v]overlay=0:0,fade=t=in:st=0:d=${FADE},fade=t=out:st=${(d - FADE).toFixed(2)}:d=${FADE},format=yuv420p[v]`;
    ff(['-f', 'lavfi', '-i', `color=c=0x101820:s=${w}x${h}:r=${FPS}:d=${d}`,
        '-loop', '1', '-framerate', String(FPS), '-t', String(d), '-i', src,
        '-loop', '1', '-framerate', String(FPS), '-t', String(d), '-i', overlayPng,
        '-filter_complex', filter, '-map', '[v]', '-t', String(d),
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-r', String(FPS), '-pix_fmt', 'yuv420p', out]);
}

// тиха фонова доріжка (синтез: акорд Am, повільна пульсація) — частина майданчиків відхиляє відео без звуку
function ambient(dur, out) {
    const tone = (f, a) => `${a}*sin(2*PI*${f}*t)`;
    const expr = `(0.55+0.45*sin(2*PI*0.08*t))*(${tone(110, 0.5)}+${tone(164.81, 0.35)}+${tone(220, 0.3)}+${tone(261.63, 0.25)}+${tone(329.63, 0.15)})`;
    ff(['-f', 'lavfi', '-i', `aevalsrc='${expr}':s=44100:d=${dur}`, '-af', `lowpass=f=1800,volume=0.16,afade=t=in:d=1.5,afade=t=out:st=${(dur - 2).toFixed(1)}:d=2`,
        '-c:a', 'aac', '-b:a', '128k', out]);
}

for (const [key, t] of Object.entries(TARGETS)) {
    if (which !== 'all' && which !== key) continue;
    const tmp = fs.mkdtempSync(path.join(process.env.TMPDIR || os.tmpdir(), `mebli-${key}-`));
    const scenes = t.spec.filter((s) => {
        const miss = [s.img].filter(Boolean).filter((f) => !fs.existsSync(path.join(ROOT, f)));
        if (miss.length) console.warn('SKIP сцену (немає файлу):', miss.join(', '));
        return !miss.length;
    });
    const pngs = await renderScenes(t.fmt, scenes, tmp);
    const clips = [];
    pngs.forEach((png, i) => {
        const sc = scenes[i], d = +sc.d, clip = path.join(tmp, `c${i}.mp4`);
        if (sc.type === 'shot' || sc.type === 'shotphone') clipShot(t.fmt, sc, png, d, clip); else clipStatic(png, d, clip);
        clips.push(clip);
    });
    fs.writeFileSync(path.join(tmp, 'list.txt'), clips.map((c) => `file '${c}'`).join('\n'));
    const silent = path.join(tmp, 'silent.mp4');
    ff(['-f', 'concat', '-safe', '0', '-i', path.join(tmp, 'list.txt'), '-c', 'copy', silent]);
    const total = parseFloat(probe(silent, 'format=duration'));
    const audio = path.join(tmp, 'ambient.m4a');
    ambient(total.toFixed(2), audio);
    const out = path.join(ROOT, 'video', t.out);
    ff(['-i', silent, '-i', audio, '-c:v', 'copy', '-c:a', 'copy', '-shortest', '-movflags', '+faststart', out]);
    console.log(key, 'готово:', out, parseFloat(probe(out, 'format=duration')).toFixed(1), 'с,', scenes.length, 'сцен');
    fs.rmSync(tmp, { recursive: true, force: true });
}
