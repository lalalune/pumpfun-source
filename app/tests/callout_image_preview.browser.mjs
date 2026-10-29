import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { createServer } from 'node:http';
import { once } from 'node:events';
import { mkdtemp, readFile, mkdir, writeFile, rm } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
const app = fileURLToPath(new URL('..', import.meta.url));
const frontend = createRequire(new URL('../packages/frontend/package.json', import.meta.url));
const backend = createRequire(new URL('../packages/backend/package.json', import.meta.url));
const { chromium } = frontend('@playwright/test'), { build } = createRequire(backend.resolve('tsx'))('esbuild');
const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');

test('complete source image owner: native motion/size/scroll/cleanup with explicit authored provider delivery at two widths', { timeout: 60000 }, async () => {
  const temp = await mkdtemp(path.join(os.tmpdir(), 'source-callout-image-')), output = process.env.PUMP_IMAGE_PREVIEW_OUTPUT;
  const requests = [], observations = [], pageErrors = [], unexpected = [];
  const packet = { domain: 'Generated source owner + realReact/nativeDOM/self-containeddataimage; authored UI-provider/Link delivery, not original752365 or product/native/visual parity', requests, observations, pageErrors, unexpected };
  let server, browser, currentPage;
  try {
    const built = await build({ absWorkingDir: app, entryPoints: [path.join(app, 'tests/fixtures/callout-image-preview.mjs')], bundle: true,
      platform: 'browser', format: 'esm', outfile: path.join(temp, 'fixture.js'), define: { 'process.env.NODE_ENV': '"development"' }, logLevel: 'silent', metafile: true });
    const bundle = await readFile(path.join(temp, 'fixture.js')); packet.bundleSha256 = sha256(bundle);
    packet.bundledInputs = [];
    for (const name of Object.keys(built.metafile.inputs).sort()) { const bytes = await readFile(path.resolve(app, name)); packet.bundledInputs.push({ path: name, bytes: bytes.length, sha256: sha256(bytes) }); }
    packet.inputs = [];
    for (const name of ['reconstruction/callout-image-preview/client.mjs', 'reconstruction/callout-image-preview/verify.mjs', 'reconstruction/callout-image-preview/PROVENANCE.json',
      'tests/fixtures/callout-image-preview.mjs', 'tests/callout_image_preview.browser.mjs', 'tests/callout_image_preview.test.mjs', 'pnpm-lock.yaml']) {
      const bytes = await readFile(path.join(app, name)); packet.inputs.push({ path: name, bytes: bytes.length, sha256: sha256(bytes) });
    }
    packet.versions = { node: process.version, react: frontend('react/package.json').version, reactDom: frontend('react-dom/package.json').version,
      esbuild: createRequire(backend.resolve('tsx'))('esbuild').version };
    server = createServer((req, res) => {
      requests.push({ method: req.method, pathAndQuery: req.url });
      if (req.method !== 'GET') { unexpected.push({ method: req.method, url: req.url }); res.writeHead(405).end(); return; }
      if (req.url === '/fixture.js') { res.setHeader('Content-Type', 'text/javascript'); res.end(bundle); }
      else if (req.url === '/') { res.setHeader('Content-Type', 'text/html'); res.end('<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Source image-preview host</title><style>body{font:16px system-ui;margin:16px}#media-scroller{height:220px;overflow:auto;border:1px solid teal}#unrelated{height:40px;overflow:auto;margin-top:8px}img{display:block;max-width:100%;height:auto}main{max-width:760px}</style><main><h1>Authored source-preview host</h1><div id="media-scroller"><div id="root"></div><div style="height:900px"></div></div><div id="unrelated"><div style="height:600px">Unrelated native scroller</div></div></main><script type="module" src="/fixture.js"></script></html>'); }
      else res.writeHead(404).end();
    });
    server.listen(0, '127.0.0.1'); await once(server, 'listening');
    const base = 'http://127.0.0.1:' + server.address().port;
    browser = await chromium.launch({ headless: true, executablePath: process.env.PUMP_BROWSER_EXECUTABLE ?? chromium.executablePath() });
    packet.versions.chromium = browser.version();
    for (const width of [390, 1280]) {
      const context = await browser.newContext({ viewport: { width, height: 844 } }), page = await context.newPage();
      currentPage = page; packet.phase = { width, stage: 'mount-and-decode' };
      page.on('pageerror', (e) => pageErrors.push({ width, message: e.message }));
      await page.route('**/*', (route) => { const r = route.request(); if (new URL(r.url()).origin !== base || r.method() !== 'GET') {
        unexpected.push({ width, method: r.method(), url: r.url() }); return route.abort(); } return route.continue(); });
      const state = () => page.evaluate(() => window.imagePreviewHarness.state());
      const wait = (value) => page.waitForFunction((value) => { const s = window.imagePreviewHarness?.state(); return s && Object.entries(value).every(([k, v]) => s[k] === v); }, value);
      await page.goto(base); await wait({ ready: true, open: false, listeners: 0 });
      const image = page.getByTestId('source-image'); await image.evaluate((image) => image.decode());
      const natural = await image.evaluate((image) => ({ width: image.naturalWidth, height: image.naturalHeight })); assert.deepEqual(natural, { width: 200, height: 100 });
      assert.equal(await image.getAttribute('loading'), 'lazy'); assert.equal(await image.getAttribute('fetchpriority'), null);
      const box = await image.boundingBox(); assert.ok(box);
      packet.phase = { width, stage: 'two-native-pointer-moves' };
      await page.mouse.move(box.x + 20, box.y + 20);
      await page.mouse.move(box.x + 30, box.y + 25);
      packet.motionSetup = { width, box, state: await state() };
      await page.waitForFunction(() => window.imagePreviewHarness.state().events.some((e) => e.type === 'native-image-move' && (e.x !== 0 || e.y !== 0)));
      packet.phase = { width, stage: 'motion-cancel-and-open' };
      await page.evaluate(() => window.imagePreviewHarness.shift(10));
      await page.waitForFunction((before) => document.querySelector('[data-testid="source-image"]').getBoundingClientRect().top > before + 5, box.y);
      const moved = await page.evaluate(() => window.imagePreviewHarness.requestOpen(true, 'trigger-hover')); assert.equal(moved.canceled, true);
      assert.equal((await state()).open, false); assert.equal((await state()).listeners, 0);
      await page.evaluate(() => window.imagePreviewHarness.shift(0));
      const allowed = await page.evaluate(() => window.imagePreviewHarness.requestOpen(true, 'trigger-focus')); assert.equal(allowed.canceled, false);
      await wait({ open: true, listeners: 1 });
      const preview = page.getByTestId('source-image-preview'); await preview.waitFor();
      const style = await preview.evaluate((image) => ({ width: image.style.getPropertyValue('--zoom-w'), ratio: image.style.getPropertyValue('--zoom-ratio'), decoding: image.decoding, draggable: image.draggable }));
      assert.deepEqual(style, { width: width === 390 ? '343px' : '600px', ratio: width === 390 ? '343 / 172' : '600 / 300', decoding: 'async', draggable: false });
      packet.phase = { width, stage: 'unrelated-then-ancestor-native-scroll' };
      await page.locator('#unrelated').evaluate((el) => { el.scrollTop = 20; });
      await page.waitForFunction(() => window.imagePreviewHarness.state().events.some((e) => e.type === 'observed-native-scroll' && e.targetId === 'unrelated'));
      assert.equal((await state()).open, true); assert.equal((await state()).listeners, 1);
      if (output) { await mkdir(output, { recursive: true }); await page.screenshot({ path: path.join(output, 'image-preview-' + width + '.png'), fullPage: true }); }
      await page.locator('#media-scroller').evaluate((el) => { el.scrollTop = 30; });
      await wait({ open: false, listeners: 0 }); assert.equal(await page.getByTestId('source-image-preview-popup').count(), 0);
      packet.phase = { width, stage: 'unmount-and-new-priority-link-lifetime' };
      await page.evaluate(() => window.imagePreviewHarness.requestOpen(true, 'trigger-focus')); await wait({ open: true, listeners: 1 });
      const beforeUnmount = await state(); await page.evaluate(() => window.imagePreviewHarness.unmount());
      assert.equal((await state()).listeners, 0); assert.equal(await image.count(), 0);
      await page.evaluate(() => window.imagePreviewHarness.mount({ priority: true, dense: true, hostHref: '/synthetic-host' }));
      await wait({ ready: true, open: false, listeners: 0 }); await image.evaluate((image) => image.decode());
      assert.equal(await image.getAttribute('loading'), 'eager'); assert.equal(await image.getAttribute('fetchpriority'), 'high');
      assert.match(await image.getAttribute('class'), /rounded-md/); assert.doesNotMatch(await image.getAttribute('class'), /authored-extra-class/);
      const host = page.getByTestId('source-image-host-link'); assert.equal(await host.getAttribute('tabindex'), '-1'); assert.equal(await host.getAttribute('aria-hidden'), 'true');
      assert.equal(await host.getAttribute('data-authored-prefetch'), 'false');
      await page.locator('#media-scroller').evaluate((el) => { el.scrollTop = 0; }); await image.click();
      assert.equal((await state()).hostClicks, 1); assert.equal(page.url(), base + '/');
      const final = await state(); assert.equal(final.events.filter((e) => e.type === 'source-listen').length, 2);
      assert.equal(final.events.filter((e) => e.type === 'source-unlisten').length, 2);
      assert.ok(final.events.filter((e) => e.type === 'source-unlisten').every((e) => e.known && e.options.capture === true));
      await page.evaluate(() => window.imagePreviewHarness.unmount()); assert.equal((await state()).listeners, 0);
      observations.push({ width, natural, moved, allowed, style, beforeUnmount, final,
        limit: 'Source callbacks/effect/DOM only; authored UI-library delivery and local Link with no original hover timing/positioning/navigation/product/visual claim' });
      await context.close();
      currentPage = undefined;
    }
    assert.deepEqual(pageErrors, []); assert.deepEqual(unexpected, []); packet.result = 'PASS';
  } catch (error) {
    packet.result = 'FAIL'; packet.failure = { name: error.name, message: error.message };
    if (currentPage && !currentPage.isClosed()) {
      try {
        packet.lastState = await currentPage.evaluate(() => window.imagePreviewHarness?.state());
        packet.lastDOM = await currentPage.evaluate(() => {
          const image = document.querySelector('[data-testid="source-image"]'), rect = image?.getBoundingClientRect();
          return { naturalWidth: image?.naturalWidth, naturalHeight: image?.naturalHeight,
            top: rect?.top, left: rect?.left, popupCount: document.querySelectorAll('[data-testid="source-image-preview-popup"]').length };
        });
      } catch (diagnosticError) { packet.diagnosticError = diagnosticError.message; }
    }
    throw error;
  }
  finally {
    await browser?.close(); if (server) { server.closeAllConnections(); await new Promise((r) => server.close(r)); }
    packet.cleanup = { browserClosed: !browser?.isConnected(), serverListening: server?.listening ?? false };
    if (output) { await mkdir(output, { recursive: true }); await writeFile(path.join(output, 'observations.json'), JSON.stringify(packet, null, 2) + '\n'); }
    await rm(temp, { recursive: true, force: true });
  }
});
