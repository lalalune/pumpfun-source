import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { APP_ROOT, recover, verify } from '../scripts/original-create-validation.mjs';
import { createFieldValidator, createParentValidate, createTextCallbacks, initialSocialErrors,
  createSocialCallbacks, createDialogCallbacks } from '../reconstruction/create-validation/client.mjs';

// Explicit external807757.W-compatible capability. No session/provider/media IO.
const validate = createFieldValidator({ utf8Bytes: (value) => new Blob([value]).size });
const fields = (overrides = {}) => ({ decodedJwt: true, name: 'Coin', ticker: 'COIN', description: '',
  image: { size: 1 }, video: undefined, banner: undefined, videoUploaded: false,
  previewStatus: 0, selectedPreview: undefined, telegram: '', website: '', twitter: '', ...overrides });
const event = (value) => ({ target: { value } });
const fail = (overrides, message) => assert.throws(() => validate(fields(overrides)), { name: 'Error', message });
function reporter() {
  const calls = [];
  const toast = { c: { error(title, options) { assert.equal(this, toast.c); calls.push(['toast', title, options.description]); } } };
  return { calls, ports: { validateFields: validate, toast, translate(key) { calls.push(['translate', key]); return 'Validation'; } } };
}
function dialogPorts(overrides = {}) {
  const calls = [];
  const ports = { walletAvailable: true, validate() { calls.push(['validate']); },
    setDialogOpen(value) { calls.push(['open', value]); }, setDialogError(value) { calls.push(['error', value]); },
    requestWalletUI(value) { calls.push(['wallet-ui', value]); },
    telemetry: { Lw(value) { assert.equal(this, undefined); calls.push(['telemetry', value]); } },
    logger: { log(value) { calls.push(['log', value]); } }, ...overrides };
  return { calls, ports };
}

test('authenticates complete field/caller/social/dialog source closure and canonical output', async () => {
  assert.deepEqual(await verify(), { factories: 5, validationCallers: 2, fields: 13, witnesses: 54 });
  const { contract } = await recover();
  assert.equal(contract.fields.length, 13);
  assert.equal(contract.dependencies.length, 4);
  assert.equal(contract.implementation.kind, 'Selected callback source model, not whole captured component or mounted UI');
  assert.ok(contract.boundaries.some((s) => s.includes('not copied') || s.includes('external') || s.includes('explicit caller capability')));
});

test('maintained verifier rejects changed client, changed contract, noncanonical bytes and missing witnesses', async () => {
  const { contract, client } = await recover();
  for (const changed of [
    Buffer.from(client.replace('T(!0)', 'T(!1)')),
    Buffer.from(client + '\n'),
  ]) await assert.rejects(verify(APP_ROOT, { client: changed }), /canonical UTF-8 bytes differ/);
  for (const change of [
    (v) => { v.fields[0].field = 'invented'; },
    (v) => { v.create.sourceNodes.pop(); },
    (v) => { v.behavior.dialog = 'false blocks opening'; },
  ]) {
    const changed = structuredClone(contract); change(changed);
    await assert.rejects(verify(APP_ROOT, { contract: Buffer.from(JSON.stringify(changed, null, 2) + '\n') }), /canonical UTF-8 bytes differ/);
  }
  await assert.rejects(verify(APP_ROOT, { contract: Buffer.from(JSON.stringify(contract)) }), /canonical UTF-8 bytes differ/);
  await assert.rejects(verify(APP_ROOT, { contract: Buffer.from(JSON.stringify(contract, null, 2) + '\n\n') }), /canonical UTF-8 bytes differ/);
  assert.equal((await readFile(path.join(APP_ROOT, 'reconstruction/create-validation/client.mjs'), 'utf8')), client);
});

test('complete first-error order starts with supplied availability, required fields and UTF-8 limits', () => {
  fail({ decodedJwt: false, name: '', ticker: '' }, 'Connect your wallet and sign in to create a coin');
  fail({ name: '', ticker: '' }, 'Coin needs a name');
  fail({ name: 'a'.repeat(33), ticker: '' }, 'Name too long: it must be less than 32 characters');
  fail({ ticker: '' }, 'Coin needs a ticker');
  fail({ ticker: 'a'.repeat(11), description: 'a'.repeat(2001) }, 'Ticker cannot be more than 10 characters');
  assert.equal(validate(fields({ name: 'a'.repeat(32), ticker: 'a'.repeat(10) })), undefined);
  assert.equal(validate(fields({ name: ' ', ticker: ' ' })), undefined, 'truthiness, no trimming');
  assert.equal(validate(fields({ decodedJwt: 'supplied-present' })), undefined, 'no token decoding or validity claim');
  fail({ name: '🪙'.repeat(9) }, 'Name too long: it must be less than 32 characters');
  assert.equal(validate(fields({ name: '🪙'.repeat(8), ticker: 'é'.repeat(5) })), undefined);
  fail({ ticker: 'é'.repeat(6) }, 'Ticker cannot be more than 10 characters');
});

test('description and ordered three file-size gates keep exact limits/copy without MIME or nonempty admission', () => {
  fail({ description: 'a'.repeat(2001), image: { size: 4500001 } }, 'Description too long');
  assert.equal(validate(fields({ description: '🪙'.repeat(1000) })), undefined, 'UTF-16 length, not codepoints or bytes');
  fail({ description: '🪙'.repeat(1001) }, 'Description too long');
  fail({ image: { size: 4500001 }, video: { size: 10000001 } }, 'Image too large: it must be less than 4.3 megabytes');
  fail({ video: { size: 10000001 }, banner: { size: 4500001 } }, 'Video too large: it must be less than 10 megabytes');
  fail({ banner: { size: 4500001 } }, 'Banner image too large: it must be under 4.5 MB');
  assert.equal(validate(fields({ image: { size: 4500000 }, banner: { size: 4500000 } })), undefined);
  assert.equal(validate(fields({ image: { size: 0, type: 'unvalidated/custom' } })), undefined, 'this gate alone checks neither type nor zero bytes');
});

test('media/readiness branches preserve precedence and distinguish supplied status2 from captured reachability', () => {
  fail({ image: undefined, banner: { size: 1 } }, 'Image or video required');
  fail({ image: undefined, video: { size: 1 }, videoUploaded: false }, 'Video not uploaded yet');
  fail({ video: { size: 1 }, videoUploaded: true }, 'Please select a thumbnail');
  fail({ videoUploaded: true, selectedPreview: '' }, 'Please select a thumbnail');
  assert.equal(validate(fields({ image: undefined, video: { size: 10000000 }, videoUploaded: true, selectedPreview: 'data:thumbnail' })), undefined);
  assert.equal(validate(fields({ videoUploaded: true, selectedPreview: ['synthetic-preview'] })), undefined, 'only truthiness/length here');
  assert.equal(validate(fields({ videoUploaded: true, previewStatus: 2 })), undefined, 'synthetic parameter branch; captured hook only initializes/resets0');
});

test('all three final social gates retain exact RegExp acceptance and first-error messages', () => {
  fail({ telegram: 't.me/name', website: 'http://example.com', twitter: 'bad' }, 'Invalid Telegram link format');
  assert.equal(validate(fields({ telegram: 'http://telegram.me/name_1', twitter: 'X.COM/user' })), undefined);
  fail({ telegram: 'https://t.me/name/' }, 'Invalid Telegram link format');
  fail({ website: 'http://example.com', twitter: 'bad' }, 'Website must use HTTPS');
  fail({ website: 'example.com' }, 'Website must include protocol (https://)');
  fail({ website: 'HTTPS://example.com' }, 'Website must include protocol (https://)');
  fail({ website: 'https://not_a_domain' }, 'Invalid Website link format');
  fail({ twitter: 'not-x/user' }, 'Invalid Twitter/X link format');
  assert.equal(validate(fields({ website: 'https://www.example.com/a?x=1', twitter: 'https://twitter.com/user?x=1' })), undefined);
});

test('raw text callbacks admit UTF-16 lengths separately from byte gate and preserve description/newlines', () => {
  const values = { name: 'old', ticker: 'OLD', description: 'old' };
  const callbacks = createTextCallbacks({ setName(v) { values.name = v; }, setTicker(v) { values.ticker = v; }, setDescription(v) { values.description = v; } });
  assert.equal(callbacks.name(event('a'.repeat(33))), undefined); assert.equal(values.name, 'old');
  callbacks.name(event('🪙'.repeat(16))); assert.equal(values.name.length, 32);
  fail({ name: values.name }, 'Name too long: it must be less than 32 characters');
  callbacks.ticker(event('a'.repeat(11))); assert.equal(values.ticker, 'OLD');
  callbacks.ticker(event('é'.repeat(10))); assert.equal(values.ticker.length, 10);
  fail({ ticker: values.ticker }, 'Ticker cannot be more than 10 characters');
  callbacks.name(event('  ')); callbacks.ticker(event(' ')); callbacks.description(event(' line1\n\nline2 '));
  assert.deepEqual(values, { name: '  ', ticker: ' ', description: ' line1\n\nline2 ' });
  callbacks.description(event('x'.repeat(2001))); assert.equal(values.description.length, 2001, 'no length admission in this setter');
});

test('social callbacks keep raw values, functional update order and isolated error state', () => {
  let errors = { ...initialSocialErrors(), website: 'old-site', twitter: 'old-x', extra: 'keep' };
  const calls = [], values = {};
  const social = createSocialCallbacks({ setTelegram(v) { calls.push(['value', 'telegram', v]); values.telegram = v; },
    setWebsite(v) { calls.push(['value', 'website', v]); values.website = v; }, setTwitter(v) { calls.push(['value', 'twitter', v]); values.twitter = v; },
    setErrors(update) { assert.equal(typeof update, 'function'); calls.push(['errors']); errors = update(errors); } });
  social.website.onChange(event(' http://example.com '));
  assert.equal(values.website, ' http://example.com ');
  assert.deepEqual(calls, [['value', 'website', ' http://example.com '], ['errors']]);
  assert.equal(errors.website, ''); assert.equal(errors.twitter, 'old-x'); assert.equal(errors.extra, 'keep');
  social.website.onBlur(event(values.website));
  assert.equal(errors.website, "Website must start with 'https://'.");
  assert.equal(values.website, ' http://example.com ', 'blur never normalizes or sets value');
  social.telegram.onChange(event('https://t.me/test')); social.twitter.onChange(event('x.com/test'));
  assert.equal(values.telegram, 'https://t.me/test'); assert.equal(values.twitter, 'x.com/test');
});

test('blur error consumers retain every branch, empty clearing and copy distinct from final validator', () => {
  let errors = initialSocialErrors();
  const noop = () => {};
  const social = createSocialCallbacks({ setTelegram: noop, setWebsite: noop, setTwitter: noop, setErrors(update) { errors = update(errors); } });
  const cases = [
    ['telegram', 'bad', 'Please enter a valid Telegram link (e.g. https://t.me/username)'],
    ['telegram', 'https://t.me/test', ''],
    ['website', 'http://example.com', "Website link cannot use 'http'. Please use 'https'."],
    ['website', 'example.com', "Website must start with 'https://'."],
    ['website', 'https://not_a_domain', 'Please enter a valid website link (e.g. https://example.com)'],
    ['website', 'https://example.com', ''],
    ['twitter', 'bad', 'Please enter a valid Twitter/X username format'],
    ['twitter', 'https://x.com/test', ''],
  ];
  for (const [key, value, expected] of cases) { social[key].onBlur(event(value)); assert.equal(errors[key], expected); }
  for (const key of Object.keys(social)) for (const value of ['', undefined]) { social[key].onBlur(event('bad')); social[key].onBlur(event(value)); assert.equal(errors[key], ''); }
});

test('parent validator uses old render snapshot values but keeps referenced media identity', () => {
  const report = reporter(), snapshot = fields({ name: '', image: { size: 1 } });
  const old = createParentValidate(snapshot, report.ports);
  snapshot.name = 'Now valid';
  assert.equal(old(), false); assert.equal(report.calls.at(-1)[2], 'Coin needs a name');
  const current = createParentValidate(snapshot, report.ports);
  assert.equal(current(), undefined);
  snapshot.image.size = 4500001;
  assert.equal(current(), false); assert.equal(report.calls.at(-1)[2], 'Image too large: it must be less than 4.3 megabytes');
});

test('parent error reporting preserves translate/toast receiver, thrown-value coercion and reporter failures', () => {
  const report = reporter();
  assert.equal(createParentValidate(fields({ name: '' }), report.ports)(), false);
  assert.deepEqual(report.calls, [['translate', 'web.create.validation_error'], ['toast', 'Validation', 'Coin needs a name']]);
  const odd = reporter(); odd.ports.validateFields = () => { throw 42; };
  assert.equal(createParentValidate(fields(), odd.ports)(), false); assert.equal(odd.calls.at(-1)[2], '42');
  const broken = reporter(), problem = Error('reporter failed'); broken.ports.toast.c.error = () => { throw problem; };
  assert.throws(createParentValidate(fields({ name: '' }), broken.ports), (e) => e === problem);
});

test('absent supplied wallet availability emits prompt then wallet UI without validation/dialog work', async () => {
  const { calls, ports } = dialogPorts({ walletAvailable: false });
  const callbacks = createDialogCallbacks(ports);
  assert.equal(callbacks.onOpenChange, ports.setDialogOpen, 'literal direct setter identity');
  assert.equal(await callbacks.onClick(), undefined);
  assert.deepEqual(calls, [['telemetry', { source: 'create' }], ['wallet-ui', true]]);
  callbacks.onOpenChange(false); assert.deepEqual(calls.at(-1), ['open', false]);
});

test('actual composed invalid fields report false yet opener opens then clears error, without submit', async () => {
  const report = reporter(), oldFields = fields({ ticker: '' });
  const parentValidate = createParentValidate(oldFields, report.ports);
  const { calls, ports } = dialogPorts({ validate() { const result = parentValidate(); calls.push(['validate-result', result]); return result; } });
  assert.equal(await createDialogCallbacks(ports).onClick(), undefined);
  assert.deepEqual(report.calls.at(-1), ['toast', 'Validation', 'Coin needs a ticker']);
  assert.deepEqual(calls, [['validate-result', false], ['open', true], ['error', undefined]]);
  // Later tn caller is a static witness in contract, never a submit invocation.
});

test('present path ignores returned Promise and catches synchronous validator/setter failures in order', async () => {
  const { calls, ports } = dialogPorts({ validate() { calls.push(['returned-promise']); return Promise.resolve(false); } });
  await createDialogCallbacks(ports).onClick();
  assert.deepEqual(calls, [['returned-promise'], ['open', true], ['error', undefined]], 'synthetic capability case, parent itself is synchronous');
  for (const thrown of [Error('bad validate'), 'opaque']) {
    const next = dialogPorts({ validate() { throw thrown; } });
    await createDialogCallbacks(next.ports).onClick();
    assert.deepEqual(next.calls, [['log', thrown], ['error', thrown instanceof Error ? thrown.message : 'an unexpected error occurred']]);
  }
  const report = reporter(), thrown = Error('toast failed'); report.ports.toast.c.error = () => { throw thrown; };
  const next = dialogPorts({ validate: createParentValidate(fields({ name: '' }), report.ports) });
  await createDialogCallbacks(next.ports).onClick();
  assert.deepEqual(next.calls, [['log', thrown], ['error', 'toast failed']]);
});

test('successful field changes through parent to supplied dialog state preserve all thirteen bindings', async () => {
  const state = fields({ name: '', ticker: '' });
  const text = createTextCallbacks({ setName(v) { state.name = v; }, setTicker(v) { state.ticker = v; }, setDescription(v) { state.description = v; } });
  text.name(event('Draft')); text.ticker(event('DRFT')); text.description(event('first\nsecond'));
  const report = reporter(), captured = [];
  const parent = createParentValidate(state, { ...report.ports, validateFields(value) { captured.push(value); return validate(value); } });
  const next = dialogPorts({ validate: parent });
  await createDialogCallbacks(next.ports).onClick();
  assert.deepEqual(captured, [state]); assert.deepEqual(Object.keys(captured[0]), Object.keys(state));
  assert.deepEqual(report.calls, []); assert.deepEqual(next.calls, [['open', true], ['error', undefined]]);
});
