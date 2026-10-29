import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir, mkdtemp, cp, rm } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { createHash } from 'node:crypto';
import { createVerifiedProfileReader, verifiedProfileKey, requireVerifiedProfilesOk,
  identityVerificationSubject, rendererVerificationSubject, rendererVerificationValue } from '../reconstruction/verified-profile/client.mjs';
import { APP_ROOT, OUTPUT, recover, verify } from '../scripts/original-verified-profile.mjs';

function timers() {
  const entries = [];
  return { entries, schedule(fn, delay) { entries.push({ fn, delay }); return entries.length - 1; },
    flush(index = 0) { assert.equal(entries[index].ran, undefined); entries[index].ran = true; entries[index].fn(); } };
}
function harness(overrides = {}) {
  const clock = timers(), requests = [], options = [];
  const cache = Array(10).fill(Symbol('uninitialized'));
  const state = { data: undefined };
  const reader = createVerifiedProfileReader({
    serverUrl: 'https://synthetic.invalid',
    schedule: clock.schedule,
    createClient: (config) => async (operation, input) => { requests.push({ config, operation, input }); return {}; },
    memo: (slots) => { assert.equal(slots, 10); return cache; },
    useQuery: (input) => { options.push(input); return state; },
    ...overrides,
  });
  return { reader, clock, requests, options, state };
}
const deferred = () => { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; };

test('source binds both complete readers, all four identity variants and the actual renderer gate', async () => {
  assert.deepEqual(await verify(), { readers: 2, identities: 4, renderer: 1 });
  const c = await recover();
  assert.equal(new Set(c.readers.map((x) => x.factory.sha256)).size, 2);
  assert.equal(c.identities.length, 4);
  assert.equal(c.behavior.capturedOrigin, 'https://frontend-api-v3.pump.fun');
  assert.match(c.behavior.query, /no final spread/);
});

test('direct read preserves Set/truthy dedup, raw response, credentials and empty-input short circuit', async () => {
  const calls = [], raw = { a: 1 };
  const h = harness({ createClient: (config) => async (operation, input) => { calls.push({ config, operation, input }); return raw; } });
  assert.deepEqual(await h.reader.readBatch('https://one.synthetic.invalid', ['', null, false, 0]), {});
  assert.equal(calls.length, 0);
  assert.strictEqual(await h.reader.readBatch('https://one.synthetic.invalid', ['a', '', 'a', ' a ', 'b']), raw);
  assert.equal(calls[0].operation, 'POST /profiles/verified');
  assert.deepEqual(calls[0].config, { clientServerUrl: 'https://one.synthetic.invalid' });
  assert.deepEqual(calls[0].input.body, { ids: ['a', ' a ', 'b'] });
  assert.equal(calls[0].input.credentials, 'same-origin');
  assert.deepEqual(Object.keys(calls[0].input), ['body', 'credentials', 'hooks']);
  assert.strictEqual(calls[0].input.hooks.afterResponse[0], requireVerifiedProfilesOk);
  assert.throws(() => createVerifiedProfileReader({}), /Explicit/);
});

test('non-ok hook and safe wrapper preserve failure-to-empty behavior without reading a service', async () => {
  assert.throws(() => requireVerifiedProfilesOk(null, null, { ok: false }), /^Error: Failed to fetch verified profiles$/);
  assert.doesNotThrow(() => requireVerifiedProfilesOk(null, null, { ok: true }));
  const marker = Error('synthetic transport');
  for (const fail of [() => { throw marker; }, async () => { throw marker; }, async () => new Response('{').json()]) {
    const h = harness({ createClient: () => fail });
    await assert.rejects(h.reader.readBatch('synthetic', ['a']));
    assert.deepEqual(await h.reader.readOrEmpty('synthetic', ['a']), {});
  }
  const h = harness({ createClient: () => async () => null });
  assert.equal(await h.reader.readOrEmpty('synthetic', ['a']), null); // no shape repair
});

test('one50ms timer groups unique keys while preserving every duplicate waiter and raw value', async () => {
  const calls = [], clock = timers();
  const h = harness({ schedule: clock.schedule, createClient: (config) => async (op, input) => {
    calls.push({ config, op, input }); return { a: true, b: 0 };
  } });
  const q = h.reader.resolverFor('one');
  assert.strictEqual(q, h.reader.resolverFor('one'));
  const a = q.fetch('a'), duplicate = q.fetch('a'), b = q.fetch('b'), absent = q.fetch('missing');
  assert.deepEqual(clock.entries.map((x) => x.delay), [50]);
  assert.equal(calls.length, 0);
  clock.flush();
  assert.deepEqual(await Promise.all([a, duplicate, b, absent]), [true, true, 0, false]);
  assert.deepEqual(calls[0].input.body.ids, ['a', 'b', 'missing']);
});

test('flush swaps pending state before asynchronous read; a later window completes independently', async () => {
  const clock = timers(), calls = [], first = deferred(), second = deferred();
  const h = harness({ schedule: clock.schedule, createClient: () => (_op, input) => {
    calls.push(input.body.ids); return calls.length === 1 ? first.promise : second.promise;
  } });
  const q = h.reader.resolverFor('one');
  let oldSettled = false;
  const old = q.fetch('old').then((x) => { oldSettled = true; return x; });
  clock.flush(0);
  const next = q.fetch('new');
  assert.equal(clock.entries.length, 2);
  clock.flush(1);
  second.resolve({ new: true });
  assert.equal(await next, true);
  assert.equal(oldSettled, false);
  first.resolve({ old: false });
  assert.equal(await old, false);
  assert.deepEqual(calls, [['old'], ['new']]);
});

test('100-key chunks and per-origin resolvers settle separately without rejection fan-out', async () => {
  const clock = timers(), calls = [];
  const h = harness({ schedule: clock.schedule, createClient: (config) => async (_op, input) => {
    const ids = input.body.ids; calls.push({ origin: config.clientServerUrl, ids });
    if (ids.length === 100) throw Error('first synthetic chunk unavailable');
    return Object.fromEntries(ids.map((id) => [id, true]));
  } });
  const one = h.reader.resolverFor('one'), two = h.reader.resolverFor('two');
  assert.notStrictEqual(one, two);
  const pending = Array.from({ length: 101 }, (_, n) => one.fetch(String(n)));
  const duplicate = one.fetch('0'), other = two.fetch('0');
  clock.flush(0); clock.flush(1);
  const values = await Promise.all(pending);
  assert.deepEqual(values.slice(0, 100), Array(100).fill(false));
  assert.equal(values[100], true);
  assert.equal(await duplicate, false);
  assert.equal(await other, true);
  assert.deepEqual(calls.map((x) => [x.origin, x.ids.length]), [['one', 100], ['one', 1], ['two', 1]]);
});

test('raw property lookup, null result and partial settlement retain the captured projection quirks', async () => {
  for (const [response, expected] of [[null, [false, false]], [{ a: '', b: 1 }, ['', 1]],
    [{ a: true, get b() { throw Error('synthetic getter'); } }, [true, false]]]) {
    const clock = timers();
    const h = harness({ schedule: clock.schedule, createClient: () => async () => response });
    const q = h.reader.resolverFor('one'), a = q.fetch('a'), b = q.fetch('b');
    clock.flush();
    assert.deepEqual(await Promise.all([a, b]), expected);
  }
  const h = harness();
  const inherited = h.reader.resolverFor('one').fetch('toString');
  h.clock.flush();
  assert.strictEqual(await inherited, Object.prototype.toString); // strict query result still rejects it
});

test('ten-slot hook memo preserves query identity, option precedence and strict true result', () => {
  const h = harness(), supplied = { enabled: true, queryKey: ['ignored'], retry: true, staleTime: 1, queryFn: () => 9 };
  h.state.data = true;
  assert.equal(h.reader.useVerifiedProfile('a', supplied), true);
  const first = h.options.at(-1);
  h.reader.useVerifiedProfile('a', supplied);
  assert.strictEqual(h.options.at(-1), first);
  h.reader.useVerifiedProfile('a', { ...supplied });
  assert.strictEqual(h.options.at(-1), first); // options identity changes but effective enabled does not
  assert.deepEqual(first.queryKey, ['user-verified', 'a']);
  assert.equal(first.retry, false);
  assert.equal(first.staleTime, 1800000);
  assert.notStrictEqual(first.queryFn, supplied.queryFn);
  for (const value of [1, 'true', {}, false, null, undefined]) {
    h.state.data = value;
    assert.equal(h.reader.useVerifiedProfile('a'), false);
  }
  assert.equal(h.requests.length, 0); // query scheduling is not invented
  for (const enabled of [false, null, 0, '']) {
    h.reader.useVerifiedProfile('a', { enabled });
    assert.strictEqual(h.options.at(-1).enabled, enabled);
  }
  assert.throws(() => h.reader.useVerifiedProfile('a', null), TypeError);
});

test('nullish keys, original callback closure and ignored query context signal remain distinct', async () => {
  const h = harness();
  h.reader.useVerifiedProfile(null);
  const nullOptions = h.options.at(-1);
  h.reader.useVerifiedProfile(undefined);
  const undefinedOptions = h.options.at(-1);
  assert.strictEqual(nullOptions.queryKey, undefinedOptions.queryKey);
  assert.notStrictEqual(nullOptions.queryFn, undefinedOptions.queryFn);
  h.reader.useVerifiedProfile('old'); const old = h.options.at(-1).queryFn;
  h.reader.useVerifiedProfile('new');
  const controller = new AbortController(); controller.abort();
  const pending = old({ signal: controller.signal });
  h.clock.flush();
  assert.equal(await pending, false);
  assert.deepEqual(h.requests[0].input.body, { ids: ['old'] });
  assert.equal('signal' in h.requests[0].input, false);
  assert.deepEqual(verifiedProfileKey(' raw '), ['user-verified', ' raw ']);
});

test('identity consumer preserves supplied userId nullish choice and verification-before-empty-view behavior', () => {
  for (const [input, expected] of [
    [{ address: 'wallet' }, 'wallet'], [{ address: 'wallet', user: { userId: 'id' } }, 'id'],
    [{ address: 'wallet', user: { userId: '' } }, ''], [{ address: 'wallet', user: { userId: null } }, 'wallet'],
    [{ user: { userId: 'id' } }, 'id'], [{ address: 'wallet', enabled: false }, undefined],
    [{ address: 'wallet', enabled: null }, undefined], [{ address: ' raw ' }, ' raw '],
  ]) assert.strictEqual(identityVerificationSubject(input), expected);
});

test('actual renderer lookup selection retains exact Near-display suppression and provided-prop precedence', () => {
  for (const [input, expected] of [
    [{ address: 'a' }, null], [{ verified: true, address: 'a' }, null],
    [{ verified: 'lookup', address: 'a' }, 'a'], [{ verified: 'lookup', address: 'a', userId: '' }, ''],
    [{ verified: 'lookup', chain: 'near:mainnet', address: 'alice' }, null],
    [{ verified: 'lookup', chain: 'near:mainnet', address: 'alice.near' }, 'alice.near'],
    [{ verified: 'lookup', chain: 'near:mainnet', address: 'ALICE.near' }, null],
    [{ verified: 'lookup', chain: 'near:mainnet', address: 'a'.repeat(64) }, 'a'.repeat(64)],
    [{ verified: 'lookup', chain: 'near:mainnet', address: '0x' + 'a'.repeat(40) }, '0x' + 'a'.repeat(40)],
    [{ verified: 'lookup', chain: 'near:mainnet', address: 'alice', userId: 'id' }, 'id'],
  ]) assert.strictEqual(rendererVerificationSubject(input), expected);
  assert.equal(rendererVerificationValue('lookup', false), false);
  assert.equal(rendererVerificationValue('lookup', true), true);
  assert.equal(rendererVerificationValue(undefined, true), false);
  assert.equal(rendererVerificationValue(null, true), null);
  assert.equal(rendererVerificationValue('provided', false), 'provided');
});

test('actual consumer subject to read/query result to badge-value model is a finite unmounted flow', async () => {
  const h = harness({ createClient: () => async (_op, input) => Object.fromEntries(input.body.ids.map((id) => [id, true])) });
  const subject = identityVerificationSubject({ address: 'wallet', user: { userId: 'profile-id' } });
  assert.equal(h.reader.useVerifiedProfile(subject), false);
  const pending = h.options.at(-1).queryFn(); h.clock.flush();
  h.state.data = await pending;
  const value = h.reader.useVerifiedProfile(subject);
  assert.equal(value, true);
  assert.equal(rendererVerificationValue('lookup', value), true);
  assert.deepEqual(h.options.at(-1).queryKey, ['user-verified', 'profile-id']);
});

test('maintained contract gate rejects changed semantics, source identity and noncanonical bytes', async () => {
  const c = await recover();
  for (const mutate of [
    (x) => { x.behavior.credentials = 'include'; },
    (x) => { x.behavior.projection = 'Boolean repair'; },
    (x) => { x.readers[0].factory.sha256 = '0'.repeat(64); },
  ]) {
    const changed = structuredClone(c); mutate(changed);
    await assert.rejects(verify(APP_ROOT, Buffer.from(JSON.stringify(changed, null, 2) + '\n')), /contract bytes differ/);
  }
  await assert.rejects(verify(APP_ROOT, Buffer.concat([await readFile(path.join(APP_ROOT, OUTPUT)), Buffer.from(' ')])), /contract bytes differ/);
});

test('raw and resealed source mutations require review without evaluating captured factories', async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'verified profile audit '));
  t.after(() => rm(root, { recursive: true, force: true }));
  const c = await recover();
  const sources = new Set([...c.readers, ...c.identities, c.renderer, ...Object.values(c.helpers)].map((x) => x.factory.source));
  for (const source of c.sharedTransport.sources) sources.add(source.source);
  const inputs = ['evidence/web/manifest.json', 'recovered/modules.json', c.implementation.path, ...Object.keys(c.dependencies), ...sources];
  for (const input of inputs) {
    const dest = path.join(root, input); await mkdir(path.dirname(dest), { recursive: true }); await cp(path.join(APP_ROOT, input), dest);
  }
  const source = c.readers[0].factory.source, original = await readFile(path.join(root, source));
  await writeFile(path.join(root, source), Buffer.concat([original, Buffer.from(' ')]));
  await assert.rejects(recover(root), /capture authentication failed/);
  const changedText = original.toString('utf8').replace('setTimeout(a,50)', 'setTimeout(a,51)');
  assert.notEqual(changedText, original.toString('utf8'));
  const changed = Buffer.from(changedText), hash = (v) => createHash('sha256').update(v).digest('hex');
  await writeFile(path.join(root, source), changed);
  const manifestPath = path.join(root, 'evidence/web/manifest.json'), manifest = JSON.parse(await readFile(manifestPath));
  manifest.records.find((x) => x.path === source).sha256 = hash(changed); await writeFile(manifestPath, JSON.stringify(manifest));
  const indexPath = path.join(root, 'recovered/modules.json'), index = JSON.parse(await readFile(indexPath));
  const variant = index.modules.find((x) => x.sha256 === c.readers[0].factory.sha256), origin = variant.origins.find((x) => x.source === source);
  variant.sha256 = hash(Buffer.from(changedText.slice(origin.start, origin.end))); await writeFile(indexPath, JSON.stringify(index));
  await assert.rejects(recover(root), /review required: changed readerA/);
});
