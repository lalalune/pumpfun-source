import test from 'node:test';
import assert from 'node:assert/strict';
import { createQuoteSelectionCoordinator } from '../reconstruction/create-quote-selection/client.mjs';
import { APP_ROOT, recover, verify } from '../scripts/original-create-quote-selection.mjs';

function setup() {
  const sentinel = Symbol.for('react.memo_cache_sentinel'), cache = Array(62).fill(sentinel), calls = [], translations = [];
  let state, opened = false, result = { data: [], isPending: false }, language = 'first';
  const mayhem = { isMayhemEnabled: false, setIsMayhemEnabled(value) { assert.equal(this, mayhem); calls.push(['mayhem', value]); this.isMayhemEnabled = value; } };
  const sharing = { enabled: false, setEnabled(value) { assert.equal(this, sharing); calls.push(['sharing', value]); this.enabled = value; } };
  const toast = { info(message) { assert.equal(this, toast); calls.push(['info', message]); } };
  let translate = (key, vars) => { translations.push({ key, vars, language }); return `${language}:${key}`; };
  const jsx = (type, props, key) => ({ type, props, key });
  const api = createQuoteSelectionCoordinator({
    createBoundStore(initialize) { state = initialize((patch) => { calls.push(['quote', patch]); state = { ...state, ...patch }; }); return (select = (s) => s) => select(state); },
    React: { useState: () => [opened, (value) => { opened = value; }] },
    compiler: (size) => size === 62 ? cache : Array(size).fill(sentinel),
    jsxRuntime: { jsx, jsxs: jsx, Fragment: 'fragment' },
    useTranslation: () => ({ t: translate }), useStocks: () => result,
    mayhemState: { getState() { calls.push(['mayhem-read']); return mayhem; } },
    feeSharingState: { getState() { calls.push(['sharing-read']); return sharing; } },
    toast, classes: (...values) => values.join(' '), Image: 'image-port', StockArt: 'stock-art-port',
    CoinAvatar: 'coin-avatar-port', Chevron: 'chevron-port', Dialog: 'dialog-port', DialogContent: 'content-port', PickerBody: 'picker-port',
  });
  function materialize(node) {
    if (!node || typeof node !== 'object') return node;
    if (Array.isArray(node)) return node.map(materialize);
    if (typeof node.type === 'function') return materialize(node.type(node.props));
    return { ...node, props: { ...node.props, children: materialize(node.props.children) } };
  }
  const view = () => materialize(api.Control());
  return { ...api, view, state: () => state, calls, translations, mayhem, sharing, toast,
    open: () => opened, stocks(data, isPending = false) { result = { data, isPending }; },
    language(next) { language = next; translate = (key, vars) => { translations.push({ key, vars, language }); return `${language}:${key}`; }; } };
}
function nodes(tree) { if (Array.isArray(tree)) return tree.flatMap(nodes); if (!tree || typeof tree !== 'object') return []; return [tree, ...nodes(tree.props?.children)]; }
const radios = (host) => nodes(host.view()).filter((n) => n.props?.role === 'radio');
const radio = (host, index) => radios(host)[index];
const picker = (host) => nodes(host.view()).find((n) => n.type === 'picker-port');
const dialog = (host) => nodes(host.view()).find((n) => n.type === 'dialog-port');
const trigger = (host) => nodes(host.view()).find((n) => n.props?.['aria-haspopup'] === 'dialog');

test('complete selected coordinator has eleven roles,41witnesses and all four source components', async () => {
  assert.deepEqual(await verify(), { sources: 11, witnesses: 41, components: 4, compilerSlots: 93, mounted: false });
  const { contract } = await recover();
  assert.deepEqual(contract.implementation.compilerSlots, [62, 10, 6, 15]);
  assert.ok(contract.witnesses.some((w) => w.label.includes('actual default Create coordinator caller')));
});

test('maintained verifier rejects changed callbacks, port handoff, variant ledger and noncanonical bytes', async () => {
  const { client, contract } = await recover();
  for (const value of [client + '\n', client.replace('name: e.name ?? e.mint', 'name: e.name || e.mint')]) {
    assert.notEqual(value, client); await assert.rejects(verify(APP_ROOT, { client: Buffer.from(value) }), /canonical source-derived bytes differ/);
  }
  for (const mutate of [(c) => c.sources.pop(), (c) => c.witnesses.pop(), (c) => { c.behavior.gateway = 'body receives open'; }, (c) => { c.implementation.compilerSlots = [62]; }]) {
    const changed = structuredClone(contract); mutate(changed);
    await assert.rejects(verify(APP_ROOT, { contract: Buffer.from(JSON.stringify(changed, null, 2) + '\n') }), /canonical source-derived bytes differ/);
  }
  await assert.rejects(verify(APP_ROOT, { contract: Buffer.from(JSON.stringify(contract)) }), /canonical source-derived bytes differ/);
});

test('actual store starts SOL; SOL/USDC radio changes derive the source flag and same-kind is a no-op', () => {
  const h = setup(); assert.deepEqual(h.state().pair, { kind: 'sol' }); assert.equal(h.state().isQuoteMintEnabled, false);
  assert.equal(radios(h).length, 2); assert.equal(radio(h, 0).props['aria-checked'], true); assert.equal(radio(h, 1).props['aria-checked'], false);
  radio(h, 1).props.onClick(); assert.deepEqual(h.state().pair, { kind: 'usdc' }); assert.equal(h.state().isQuoteMintEnabled, true);
  const count = h.calls.length; radio(h, 1).props.onClick(); assert.equal(h.calls.length, count);
  radio(h, 0).props.onClick(); assert.deepEqual(h.state().pair, { kind: 'sol' }); assert.equal(h.state().isQuoteMintEnabled, false);
  assert.ok(!h.calls.some(([kind]) => kind === 'mayhem-read' || kind === 'sharing-read'));
});

test('third radio gate, selected appearance and pending query handoff follow only supplied data/current kind', () => {
  const h = setup(); h.stocks(undefined, true); assert.equal(radios(h).length, 2);
  const stock = { mint: 'synthetic-stock', symbol: 'Stock', ticker: 'STK' }; h.stocks([stock]);
  assert.equal(radios(h).length, 3); radio(h, 2).props.onClick();
  h.stocks(null, true); assert.equal(radios(h).length, 3); assert.equal(radio(h, 2).props['aria-checked'], true);
  assert.equal(h.state().pair.kind, 'stock'); assert.ok(trigger(h)); trigger(h).props.onClick();
  assert.equal(picker(h).props.isLoading, true); assert.deepEqual(picker(h).props.stocks, []);
  assert.equal(picker(h).props.isOpen, undefined, 'body is five-field contract, not six-field gateway');
});

test('stock radio reads current flags and invokes setters/toasts before pair change in source order', () => {
  const h = setup(); h.stocks([{ mint: 's', symbol: 'Stock', ticker: 'S' }]);
  const oldRadio = radio(h, 2); h.mayhem.isMayhemEnabled = true; h.sharing.enabled = true;
  oldRadio.props.onClick();
  assert.deepEqual(h.calls.map(([kind]) => kind), ['mayhem-read', 'mayhem', 'info', 'sharing-read', 'sharing', 'info', 'quote']);
  assert.deepEqual(h.calls[1], ['mayhem', false]); assert.deepEqual(h.calls[4], ['sharing', false]);
  assert.match(h.calls[2][1], /pair_stock_mayhem_unsupported$/); assert.match(h.calls[5][1], /pair_stock_fee_sharing_unsupported$/);
  assert.deepEqual(h.state().pair, { kind: 'stock' });
  const count = h.calls.length; radio(h, 2).props.onClick(); assert.equal(h.calls.length, count);
});

test('flag/toast capability errors preserve actual propagation and do not add launch-admission repair', () => {
  const h = setup(); h.stocks([{ mint: 's', symbol: 'Stock', ticker: 'S' }]); h.mayhem.isMayhemEnabled = true; h.sharing.enabled = true;
  const error = Error('synthetic toast failed'); h.toast.info = () => { throw error; };
  assert.throws(() => radio(h, 2).props.onClick(), (e) => e === error);
  assert.equal(h.mayhem.isMayhemEnabled, false); assert.equal(h.sharing.enabled, true); assert.equal(h.state().pair.kind, 'sol');
});

test('dialog gateway mounts only open body, passes five exact fields and ignores true open notifications', () => {
  const h = setup(); h.store().setPair({ kind: 'stock' }); assert.equal(picker(h), undefined);
  trigger(h).props.onClick(); assert.equal(h.open(), true); assert.equal(dialog(h).props.isOpen, true);
  assert.deepEqual(Object.keys(picker(h).props).filter((k) => k !== 'children'), ['isLoading', 'stocks', 'onSelect', 'onSelectPumpCoin', 'onClose']);
  dialog(h).props.onIsOpenChange(true); assert.equal(h.open(), true);
  dialog(h).props.onIsOpenChange(false); assert.equal(h.open(), false); assert.equal(picker(h), undefined);
});

test('stock body callback preserves object identity, closes and does not repeat the radio flag branch', () => {
  const h = setup(), stock = { mint: 's', symbol: '', ticker: '', nested: { retained: true } };
  h.store().setPair({ kind: 'stock' }); trigger(h).props.onClick();
  h.mayhem.isMayhemEnabled = true; h.sharing.enabled = true; h.calls.length = 0;
  picker(h).props.onSelect(stock);
  assert.equal(h.state().pair.stock, stock); assert.equal(h.open(), false);
  assert.equal(h.mayhem.isMayhemEnabled, true); assert.equal(h.sharing.enabled, true);
  assert.deepEqual(h.calls.map(([kind]) => kind), ['quote']);
});

test('Pump body callback keeps full shallow spread and nullish fallback without replacing empty strings', () => {
  const h = setup(), nested = { retained: true };
  h.store().setPair({ kind: 'stock' }); trigger(h).props.onClick();
  const missing = { mint: 'p', name: null, nested, unrelated: 12 };
  picker(h).props.onSelectPumpCoin(missing);
  assert.equal(h.state().pair.kind, 'pump'); assert.notEqual(h.state().pair.coin, missing);
  assert.deepEqual(h.state().pair.coin, { mint: 'p', name: 'p', symbol: 'p', nested, unrelated: 12 });
  assert.equal(h.state().pair.coin.nested, nested); assert.equal(h.open(), false);
  trigger(h).props.onClick(); picker(h).props.onSelectPumpCoin({ mint: 'p2', name: '', symbol: '' });
  assert.deepEqual(h.state().pair.coin, { mint: 'p2', name: '', symbol: '' });
  // Defensive synthetic callback branches do not establish original search eligibility.
});

test('quote-store enabled setter and selected-record/art/translation handoff keep source fields', () => {
  const h = setup(), stock = { mint: 's', symbol: 'Stock name', ticker: 'STK' };
  h.store().setPair({ kind: 'stock', stock }); h.view();
  assert.ok(h.translations.some((c) => c.key === 'web.create.pair_with_stock' && c.vars.symbol === stock.symbol && c.vars.ticker === stock.ticker));
  assert.equal(nodes(h.view()).find((n) => n.type === 'stock-art-port').props.stock, stock);
  const coin = { mint: 'p', name: 'Pump name', symbol: 'PMP' }; h.store().setPair({ kind: 'pump', coin }); h.view();
  assert.ok(h.translations.some((c) => c.vars?.ticker === coin.name && c.vars.symbol === coin.symbol));
  assert.equal(nodes(h.view()).find((n) => n.type === 'coin-avatar-port').props.coin, coin);
  h.store().setIsQuoteMintEnabled(true); assert.deepEqual(h.state().pair, { kind: 'usdc' }); assert.equal(h.state().isQuoteMintEnabled, true);
  h.store().setIsQuoteMintEnabled(false); assert.deepEqual(h.state().pair, { kind: 'sol' }); assert.equal(h.state().isQuoteMintEnabled, false);
});

test('open state is independent of quote changes and original gateway close callback still owns closure', () => {
  const h = setup(); h.store().setPair({ kind: 'stock' }); trigger(h).props.onClick(); const oldBody = picker(h);
  h.store().setPair({ kind: 'sol' }); assert.equal(trigger(h), undefined); assert.equal(h.open(), true); assert.ok(picker(h));
  oldBody.props.onClose(); assert.equal(h.open(), false);
});
