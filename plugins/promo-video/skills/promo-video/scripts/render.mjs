#!/usr/bin/env node
// Frame-accurate renderer for code-driven videos.
//
// The page must expose:
//   window.seek(t)     draw the exact frame for time t (seconds); may be sync or async
//   window.DURATION    total length in seconds
//   window.ready       (optional) promise to await before the first frame, e.g. font preloading
//
// Usage (run from the project folder so Playwright resolves from its node_modules):
//   node render.mjs promo.html stills 0.5 3.2 9.9         -> stills/NNN_tSS.ss.png
//   node render.mjs promo.html sheet 0.5 3.2 9.9 --cols 4 -> contact.png (labelled grid of those frames)
//   node render.mjs promo.html sheet --every 1.5          -> contact sheet sampled every 1.5 s
//   node render.mjs promo.html video --fps 60 --out out/video-silent.mp4
// Common flags: --size 1920x1080 (or 1080x1920, 1080x1080), --chrome /path/to/chrome, --query "w=1080&h=1920"
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const argv = process.argv.slice(2);
const flags = {};
const pos = [];
for (let i = 0; i < argv.length; i++) {
  if (argv[i].startsWith('--')) { flags[argv[i].slice(2)] = argv[i + 1]; i++; } else pos.push(argv[i]);
}
const [pageArg, mode = 'stills', ...times] = pos;
if (!pageArg) { console.error('usage: node render.mjs <page.html> <stills|sheet|video> [times...] [--flags]'); process.exit(1); }
const [W, H] = (flags.size || '1920x1080').split('x').map(Number);

// Resolve Playwright from the current project, not from wherever this script lives.
async function loadChromium() {
  const req = createRequire(path.join(process.cwd(), 'noop.js'));
  for (const name of ['playwright', 'playwright-core']) {
    try {
      const mod = await import(pathToFileURL(req.resolve(name)).href);
      const chromium = mod.chromium || mod.default?.chromium;   // CommonJS packages arrive under .default
      if (chromium) return chromium;
    } catch {}
  }
  console.error('Playwright not found here. Run: npm i playwright-core   (or npm i playwright && npx playwright install chromium)');
  process.exit(1);
}
const CHROME_CANDIDATES = [
  flags.chrome, process.env.CHROME_PATH,
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser',
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
].filter(Boolean);
async function launch(chromium) {
  const args = ['--force-color-profile=srgb', '--hide-scrollbars', '--font-render-hinting=none'];
  try { return await chromium.launch({ args }); } catch (e) {
    for (const p of CHROME_CANDIDATES) if (existsSync(p)) return chromium.launch({ executablePath: p, args });
    throw e;
  }
}

const chromium = await loadChromium();
const browser = await launch(chromium);
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('page error:', e.message));
const url = pathToFileURL(path.resolve(pageArg)).href + (flags.query ? `?${flags.query}` : '');
await page.goto(url);
await page.waitForFunction(() => typeof window.seek === 'function', null, { timeout: 15000 });
await page.evaluate(async () => { if (window.ready) await window.ready; await document.fonts.ready; });
await page.waitForFunction(() => [...document.images].every(i => i.complete));
const duration = await page.evaluate(() => window.DURATION);

const frame = async t => {
  await page.evaluate(async t => { await window.seek(t); }, t);
  return page.screenshot({ type: 'png' });
};
const sampleTimes = () => {
  if (flags.every) { const out = []; for (let t = 0; t < duration; t += Number(flags.every)) out.push(+t.toFixed(3)); return out; }
  return times.map(Number);
};

if (mode === 'stills' || mode === 'sheet') {
  const ts = sampleTimes();
  const shots = [];
  const dir = flags.dir || 'stills';
  mkdirSync(dir, { recursive: true });
  for (const [i, t] of ts.entries()) {
    const buf = await frame(t);
    shots.push({ t, buf });
    if (mode === 'stills') writeFileSync(path.join(dir, `${String(i + 1).padStart(3, '0')}_t${t.toFixed(2).padStart(6, '0')}.png`), buf);
  }
  if (mode === 'sheet') {
    const cols = Number(flags.cols || 4), cellW = Math.floor(Number(flags.cellw || 640));
    const cellH = Math.round(cellW * H / W);
    const html = `<body style="margin:0;background:#fff;font:600 18px -apple-system,system-ui,sans-serif">
      <div style="display:grid;grid-template-columns:repeat(${cols},${cellW}px);gap:8px;padding:8px">
      ${shots.map(s => `<div><img style="display:block;width:${cellW}px;height:${cellH}px" src="data:image/png;base64,${s.buf.toString('base64')}"><div style="padding:4px 2px">${s.t.toFixed(2)}s</div></div>`).join('')}
      </div></body>`;
    const sheet = await browser.newPage({ viewport: { width: cols * (cellW + 8) + 8, height: 400 } });
    await sheet.setContent(html);
    const out = flags.out || 'contact.png';
    await sheet.screenshot({ path: out, fullPage: true });
    console.log(`wrote ${out} (${shots.length} frames)`);
  } else console.log(`wrote ${shots.length} stills to ${dir}/`);
} else if (mode === 'video') {
  const fps = Number(flags.fps || 60);
  const from = Number(flags.from || 0), to = Math.min(Number(flags.to || duration), duration);
  const total = Math.round((to - from) * fps);
  const out = flags.out || 'out/video-silent.mp4';
  mkdirSync(path.dirname(out), { recursive: true });
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', flags.preset || 'slow', '-crf', flags.crf || '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const started = Date.now();
  for (let i = 0; i < total; i++) {
    const buf = await frame(from + i / fps);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % (fps * 5) === 0) console.log(`frame ${i}/${total} (${((Date.now() - started) / 1000).toFixed(0)}s)`);
  }
  ff.stdin.end();
  const code = await new Promise(r => ff.on('close', r));
  console.log(code === 0 ? `wrote ${out}: ${total} frames in ${((Date.now() - started) / 1000).toFixed(0)}s` : `ffmpeg exited ${code}`);
} else {
  console.error(`unknown mode ${mode}`);
}
await browser.close();
