import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { mkdtemp, mkdir, readFile, writeFile, copyFile, link, symlink, rm } from 'node:fs/promises';
import { promisify } from 'node:util';
import { execFile } from 'node:child_process';
import path from 'node:path';
import os from 'node:os';
import { createCalloutImagePreview, CALLOUT_PREVIEW_CLASS } from '../reconstruction/callout-image-preview/client.mjs';
import { APP_ROOT, DIRECTORY, verify } from '../reconstruction/callout-image-preview/verify.mjs';

function descriptors({ props = {}, viewport = { innerWidth: 1000, innerHeight: 800 } } = {}) {
  const memo = Array(35).fill(Symbol.for('react.memo_cache_sentinel')), refs = [], actions = [], effects = [];
  let stateIndex = 0;
  const HoverCard = Object.fromEntries(['Root', 'Trigger', 'Portal', 'Positioner', 'Popup'].map((n) => [n, 'host:' + n]));
  const jsx = (type, props) => ({ type, props });
  class NativeNode {}
  const ports = { jsx, jsxs: jsx, useMemoCache: (n) => { assert.equal(n, 35); return memo; },
    React: { useRef: (value) => { const ref = { current: value }; refs.push(ref); return ref; },
      useState: (value) => { const index = stateIndex++; return [value, (next) => actions.push([index, next])]; },
      useEffect: (...args) => effects.push(args) },
    HoverCard, Link: 'host:Link', classNames: (...xs) => xs.filter(Boolean).join(' '),
    document: { addEventListener() {}, removeEventListener() {} }, window: viewport, Node: NativeNode };
  const Preview = createCalloutImagePreview(ports), root = Preview({ src: 'synthetic:data-image', testId: 'synthetic-media', ...props });
  const [host, portal] = root.props.children;
  const trigger = host.type === 'host:Link' ? host.props.children : host;
  return { ports, root, host, trigger, portal, refs, actions, effects };
}
test('source closes all three complete owners, shared UI aliases and three real caller descriptors', async () => {
  const p = await verify(); assert.equal(p.frames.length, 3);
  assert.equal(new Set(p.frames.map((f) => f.normalizedSha256)).size, 1);
  assert.equal(p.caller.calls.length, 3);
  assert.match(p.ports.HoverCard, /one instance/); assert.match(p.limits.join(' '), /implementation/);
});
test('actual motion gate cancels changed hover top and preserves zero-motion/other-reason behavior', () => {
  const h = descriptors(); let top = 50, reads = 0, canceled = 0;
  const image = { naturalWidth: 200, naturalHeight: 100, getBoundingClientRect() { reads++; return { top }; } };
  h.refs[0].current = image;
  h.trigger.props.onMouseEnter();
  h.trigger.props.onMouseMove({ nativeEvent: { movementX: 0, movementY: 0 }, currentTarget: image });
  assert.equal(reads, 0); assert.equal(h.refs[1].current, null);
  h.trigger.props.onMouseMove({ nativeEvent: { movementX: 1, movementY: 0 }, currentTarget: image });
  assert.equal(h.refs[1].current, 50); top = 55;
  h.root.props.onOpenChange(true, { reason: 'trigger-hover', cancel() { canceled++; } });
  assert.equal(canceled, 1); assert.deepEqual(h.actions, []);
  h.root.props.onOpenChange(true, { reason: 'trigger-focus', cancel() { assert.fail('non-hover must bypass motion gate'); } });
  assert.deepEqual(h.actions, [[0, true], [1, { width: 600, height: 300 }]]);
  h.actions.length = 0; h.root.props.onOpenChange(false, { reason: 'escape-key' });
  assert.deepEqual(h.actions, [[0, false]]);
});
test('complete open callback retains viewport fit/rounding/3x cap and invalid-size arithmetic', () => {
  for (const [width, height, viewport, expected] of [
    [200, 100, { innerWidth: 390, innerHeight: 844 }, { width: 343, height: 172 }],
    [1000, 1000, { innerWidth: 1280, innerHeight: 844 }, { width: 709, height: 709 }],
    [10, 20, { innerWidth: 5000, innerHeight: 5000 }, { width: 30, height: 60 }],
    [0, 100, { innerWidth: 390, innerHeight: 844 }, null],
    [10, 20, { innerWidth: 0, innerHeight: 0 }, null],
  ]) {
    const h = descriptors({ viewport }); h.refs[0].current = { naturalWidth: width, naturalHeight: height };
    h.root.props.onOpenChange(true, { reason: 'trigger-focus' });
    assert.deepEqual(h.actions, [[0, true], [1, expected]]);
  }
  const h = descriptors(); h.refs[0].current = { naturalWidth: NaN, naturalHeight: 100 };
  h.root.props.onOpenChange(true, { reason: 'trigger-focus' });
  assert.ok(Number.isNaN(h.actions[1][1].width)); assert.ok(Number.isNaN(h.actions[1][1].height));
  const empty = descriptors(); empty.root.props.onOpenChange(true, { reason: 'trigger-focus' });
  assert.deepEqual(empty.actions, [[0, true], [1, null]]);
});
test('priority/density/host-link and popup descriptors preserve original delivery contracts', () => {
  const click = () => {}, h = descriptors({ props: { priority: true, dense: true, className: 'synthetic-class', hostHref: '/synthetic-host', onHostClick: click } });
  assert.equal(h.host.type, 'host:Link'); assert.equal(h.host.props.href, '/synthetic-host');
  assert.equal(h.host.props.prefetch, false); assert.equal(h.host.props.tabIndex, -1);
  assert.equal(h.host.props['aria-hidden'], 'true'); assert.strictEqual(h.host.props.onClick, click);
  const image = h.trigger.props.render.props;
  assert.equal(image.loading, 'eager'); assert.equal(image.fetchPriority, 'high');
  assert.match(image.className, /rounded-md/); assert.doesNotMatch(image.className, /synthetic-class/);
  assert.equal(h.trigger.props.delay, 600); assert.equal(h.trigger.props.closeDelay, 100);
  assert.equal(h.portal.type, 'host:Portal');
  const positioner = h.portal.props.children, popup = positioner.props.children, preview = popup.props.children;
  assert.equal(positioner.props.side, 'right'); assert.equal(positioner.props.align, 'start');
  assert.equal(positioner.props.sideOffset, 12); assert.equal(positioner.props.collisionPadding, 16);
  assert.equal(popup.props['data-testid'], 'synthetic-media-preview-popup');
  assert.ok(popup.props.className.includes(CALLOUT_PREVIEW_CLASS));
  assert.equal(preview.props.decoding, 'async'); assert.equal(preview.props.draggable, false);
  assert.equal(preview.props.style, undefined);
  const plain = descriptors(); assert.equal(plain.trigger.props.render.props.loading, 'lazy');
  assert.equal(plain.trigger.props.render.props.fetchPriority, undefined);
  assert.equal(plain.effects.length, 1); assert.equal(plain.effects[0][0](), undefined);
});
test('installed React/compiler SSR renders actual inline source without acquiring DOM or remote state', () => {
  const require = createRequire(new URL('../packages/frontend/package.json', import.meta.url));
  const React = require('react'), { c } = require('react/compiler-runtime'), jsx = require('react/jsx-runtime'), { renderToString } = require('react-dom/server');
  const Context = React.createContext(null);
  const HoverCard = { Root: ({ children, ...value }) => React.createElement(Context.Provider, { value }, children),
    Trigger: ({ render }) => render, Portal: ({ children }) => children, Positioner: ({ children }) => children,
    Popup: ({ children }) => React.useContext(Context).open ? children : null };
  const Preview = createCalloutImagePreview({ ...jsx, React, useMemoCache: c, HoverCard,
    Link: ({ children }) => children, classNames: (...xs) => xs.filter(Boolean).join(' '),
    document: { addEventListener() { assert.fail('SSR must not subscribe'); }, removeEventListener() {} },
    window: { get innerWidth() { assert.fail('SSR must not read viewport'); } }, Node: class {} });
  const html = renderToString(React.createElement(Preview, { src: 'data:image/svg+xml,synthetic', testId: 'ssr-media' }));
  assert.match(html, /data-testid="ssr-media"/); assert.match(html, /loading="lazy"/);
  assert.doesNotMatch(html, /preview-popup/);
});
test('no implicit renderer, provider instance, Link or DOM capabilities', () => {
  const h = descriptors();
  for (const name of ['jsx', 'jsxs', 'useMemoCache', 'classNames', 'Node'])
    assert.throws(() => createCalloutImagePreview({ ...h.ports, [name]: undefined }), /Explicit/);
  assert.throws(() => createCalloutImagePreview({ ...h.ports, HoverCard: {} }), /same-instance/);
  assert.throws(() => createCalloutImagePreview({ ...h.ports, document: {} }), /event capabilities/);
});
test('public input-only CLI and source mutations preserve original bytes and all variants', async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'callout image public inputs ')); t.after(() => rm(root, { recursive: true, force: true }));
  const p = JSON.parse(await readFile(path.join(APP_ROOT, DIRECTORY, 'PROVENANCE.json'), 'utf8'));
  async function copy(name, immutable = false) {
    const to = path.join(root, name); await mkdir(path.dirname(to), { recursive: true });
    if (immutable) { try { await link(path.join(APP_ROOT, name), to); return; } catch (e) { if (e.code !== 'EXDEV') throw e; } }
    await copyFile(path.join(APP_ROOT, name), to);
  }
  for (const name of ['evidence/web/manifest.json', 'recovered/modules.json', DIRECTORY + '/client.mjs', DIRECTORY + '/verify.mjs', DIRECTORY + '/PROVENANCE.json',
    'scripts/original-contracts/source.mjs', 'scripts/verify-search-session.mjs']) await copy(name);
  const sources = [...new Set([...p.factories.map((f) => f.source), p.style.factory.source, p.caller.factory.source])];
  for (const name of sources) await copy(name, true);
  await symlink(path.join(APP_ROOT, 'node_modules'), path.join(root, 'node_modules'));
  const out = await promisify(execFile)(process.execPath, [path.join(root, DIRECTORY, 'verify.mjs'), '--check'], { cwd: root }); assert.match(out.stdout, /PASS complete35-slot/);
  const client = path.join(root, DIRECTORY, 'client.mjs'), original = await readFile(client, 'utf8');
  assert.ok(original.includes('delay: 600')); await writeFile(client, original.replace('delay: 600', 'delay: 500'));
  await assert.rejects(verify(root), /module differs/); await writeFile(client, original);
  const index = path.join(root, 'recovered/modules.json'), initial = await readFile(index, 'utf8'), changed = JSON.parse(initial);
  changed.modules.splice(changed.modules.findIndex((m) => m.ids.includes(364889)), 1); await writeFile(index, JSON.stringify(changed));
  await assert.rejects(verify(root), /all three/); await writeFile(index, initial);
  const raw = path.join(root, sources[0]), bytes = await readFile(raw); await rm(raw); await writeFile(raw, Buffer.concat([bytes, Buffer.from(' ')]));
  await assert.rejects(verify(root), (e) => e.message === `capture authentication failed: ${sources[0]}`);
});
