// Films template/index.html with a timeline.json, frame by frame, in parallel chunks.
//   node template/render.js <timeline.json> <out_silent.mp4> [workers]
//   node template/render.js <timeline.json> --stills 2.0,9.5 <outdir>
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const FFARGS = ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', '30', '-g', '60'];

async function openPage(browser, timeline) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => { console.error('[pageerror]', e.message); process.exitCode = 1; });
  await page.addInitScript(tl => { window.TIMELINE = tl; }, timeline);
  await page.goto('file://' + path.resolve(__dirname, 'index.html'));
  await page.evaluate(() => window.ready);
  return page;
}

async function renderChunk(browser, timeline, f0, f1, out) {
  const page = await openPage(browser, timeline);
  const tmp = out.replace(/\.mp4$/, '.part.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '30', '-c:v', 'mjpeg', '-i', '-', ...FFARGS, tmp],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let f = f0; f < f1; f++) {
    await page.evaluate(t => window.renderFrame(t), f / 30);
    const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - f0) % 150 === 0) console.log(`${path.basename(out)}: frame ${f}/${f1} (${((Date.now() - t0) / (f - f0 + 1)).toFixed(0)} ms/frame)`);
  }
  ff.stdin.end();
  const code = await new Promise(r => ff.on('close', r));
  if (code !== 0) throw new Error('ffmpeg exited ' + code);
  fs.renameSync(tmp, out);
  await page.close();
}

(async () => {
  const [tlPath, out, arg3, arg4] = process.argv.slice(2);
  const timeline = JSON.parse(fs.readFileSync(tlPath, 'utf8'));
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });

  if (out === '--stills') {
    const page = await openPage(browser, timeline);
    fs.mkdirSync(arg4, { recursive: true });
    for (const t of arg3.split(',').map(Number)) {
      await page.evaluate(t => window.renderFrame(t), t);
      await page.screenshot({ path: path.join(arg4, `still_${t.toFixed(2)}.jpg`), type: 'jpeg', quality: 92 });
    }
  } else {
    const total = Math.ceil(timeline.end * 30);
    const workers = Math.max(1, +(arg3 || Math.min(4, os.cpus().length)));
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'reelio-'));
    const per = Math.ceil(total / workers);
    const parts = [];
    for (let i = 0; i < workers; i++) {
      const f0 = i * per, f1 = Math.min(total, f0 + per);
      if (f0 < f1) parts.push({ f0, f1, file: path.join(dir, `p${String(i).padStart(2, '0')}.mp4`) });
    }
    await Promise.all(parts.map(p => renderChunk(browser, timeline, p.f0, p.f1, p.file)));
    fs.writeFileSync(path.join(dir, 'list.txt'), parts.map(p => `file '${p.file}'`).join('\n'));
    await new Promise((res, rej) => spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', path.join(dir, 'list.txt'), '-c', 'copy', out],
      { stdio: 'inherit' }).on('close', c => c === 0 ? res() : rej(new Error('concat failed'))));
    console.log('rendered', out);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
