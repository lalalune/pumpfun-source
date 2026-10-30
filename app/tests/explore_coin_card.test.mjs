import assert from 'node:assert/strict';
import test from 'node:test';
import { createRequire } from 'node:module';
import { mkdtemp, mkdir, copyFile, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { createExploreCoinCard, CARD_CONTEXTS } from '../reconstruction/explore-coin-card/client.mjs';
import { createCoinCardFixture } from '../reconstruction/explore-coin-card/fixture.mjs';
import { verify, recover, APP_ROOT } from '../reconstruction/explore-coin-card/recover.mjs';
const require = createRequire(new URL('../packages/frontend/package.json', import.meta.url));
const React = require('react'), jsx = require('react/jsx-runtime'), compiler = require('react/compiler-runtime');
const { renderToStaticMarkup } = require('react-dom/server');
const make = (context) => createCoinCardFixture({ React, jsx, compiler, context });
const render = (Component, props) => renderToStaticMarkup(jsx.jsx(Component, props));

test('complete two-context Card owners and actual MAIN grid admission regenerate', async () => {
  const proof = await verify();
  assert.equal(proof.contexts.length, 2);
  assert.deepEqual(proof.admission.cardContexts.map(({ initialScript }) => initialScript), [false, true]);
  assert.equal(proof.admission.props.label, 'complete actual Card prop handoff');
  for (const context of proof.contexts) {
    assert.equal(context.imports.length, 46);
    assert.deepEqual(context.prerequisites.map(({ id }) => id), [12692, 107240]);
  }
});

test('explicit context, initialized modules and actual host roles are required', () => {
  const f = make();
  const input = { context: CARD_CONTEXTS[1], React, jsx, compiler, Avatar: f.Avatar, formatters: f.formatters, modules: f.modules, host: f.host, loadModule() {} };
  assert.throws(() => createExploreCoinCard({ ...input, context: 'unknown' }), /context/);
  f.modules.delete(107240);
  assert.throws(() => createExploreCoinCard(input), /107240/);
  f.modules.set(107240, {});
  const { setInterval, ...host } = f.host;
  assert.throws(() => createExploreCoinCard({ ...input, host }), /setInterval/);
});

for (let index = 0; index < CARD_CONTEXTS.length; index++) {
  test(`context${index}: full Card read/display descriptors and source inline SVG are retained`, () => {
    const f = make(CARD_CONTEXTS[index]);
    const html = render(f.flow.Card, f.props);
    assert.match(html, /synthetic coin/); assert.match(html, /synthetic description/);
    assert.match(html, /href="\/coin\/A"/); assert.match(html, /compact:100/);
    assert.match(html, /M0,90 L100,10/);
    assert.match(html, /web.mayhem.mode_multiplayer/); assert.match(html, /creator_fees.charity.label/);
    assert.deepEqual(f.calls.chartQuery.at(-1), { coinAddress: 'A', coinCreatedTimestamp: 1700000000, chainId: 'solana', queryOptions: { enabled: true, staleTime: 300000, gcTime: 600000 } });
    assert.deepEqual(f.calls.creatorQuery.at(-1), { address: f.props.coin.creator, enabled: true });
    assert.equal(f.calls.media.at(-1).width, 600); assert.equal(f.calls.media.at(-1).eager, true); assert.equal(f.calls.media.at(-1).priority, true);
    assert.equal(f.calls.badge.at(-1).chainSize, 20);
    assert.equal(f.calls.intervals.size, 0, 'SSR null snapshot does not subscribe the original module clock');
  });

  test(`context${index}: module clock is shared, samples callback-time now and clears only after last subscriber`, () => {
    const f = make(CARD_CONTEXTS[index]), seen = [];
    assert.equal(f.flow.clockServerSnapshot(), null);
    const one = f.flow.subscribeClock(() => seen.push(['one', f.flow.clockSnapshot()]));
    const two = f.flow.subscribeClock(() => seen.push(['two', f.flow.clockSnapshot()]));
    assert.equal(f.calls.intervals.size, 1);
    assert.equal([...f.calls.intervals.values()][0].delay, 60000);
    f.tick(1700000061000);
    assert.deepEqual(seen, [['one', 1700000061000], ['two', 1700000061000]]);
    one(); assert.equal(f.calls.intervals.size, 1);
    two(); assert.equal(f.calls.intervals.size, 0);
  });
}

test('live status suppresses Mayhem while strict multiplayer and truthy timestamp policies remain', () => {
  const f = make();
  const live = render(f.flow.Card, { ...f.props, coin: { ...f.props.coin, is_currently_live: true } });
  assert.match(live, /web.nav.live/); assert.doesNotMatch(live, /web.mayhem.mode_multiplayer/);
  const zero = render(f.flow.Card, { ...f.props, coin: { ...f.props.coin, created_timestamp: 0, mayhem_is_multiplayer: 1, is_charity: false } });
  assert.match(zero, /web.nav.mayhem/); assert.doesNotMatch(zero, /web.mayhem.mode_multiplayer/);
  assert.match(zero, /—/);
  assert.equal(f.calls.chartQuery.at(-1).queryOptions.enabled, false);
});

test('creator query values override only nullishly; Avatar and accepted profile routing stay explicit', () => {
  const f = make(); f.state.creator = { username: '', profile_image: '' };
  const html = render(f.flow.Card, f.props);
  assert.doesNotMatch(html, /original-us/);
  assert.equal(f.calls.avatars.at(-1).src, '');
  assert.equal(f.calls.avatars.at(-1).isAnonymous, true);
  assert.equal(f.calls.avatars.at(-1).address, f.props.coin.creator);
  assert.match(html, /creator/);
});

test('market-cap formatting default and inline flat-point normalization add no data validation', () => {
  const f = make();
  assert.match(render(f.flow.MarketCap, {}), /compact:0/);
  assert.match(render(f.flow.MarketCap, { value: 99, transition: { duration: 1 } }), /compact:99/);
  f.state.points = [{ price: 5 }, { price: 5 }];
  const flat = render(f.flow.Card, f.props);
  assert.match(flat, /M0,90 L100,90/);
  f.state.points = [];
  const empty = render(f.flow.Card, f.props);
  assert.doesNotMatch(empty, /glow-A/);
});

test('media frame carries exact platform/program/priority input without fetching an image', () => {
  const f = make(), coin = { ...f.props.coin, board_program: 'board', protocol: 'protocol', platform: 'platform', program: 'program' };
  render(f.flow.Media, { coin, eager: false, priority: true });
  assert.deepEqual(f.calls.media.at(-1), { coin, width: 600, height: 600, eager: false, priority: true });
  assert.equal(f.calls.badge.at(-1).boardProgram, 'board');
  assert.equal(f.calls.badge.at(-1).protocol, 'protocol');
});

test('portable public-input export authenticates both complete owners and rejects changed capture bytes', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'explore-card-'));
  try {
    const proof = await verify();
    const paths = ['evidence/web/manifest.json', 'recovered/modules.json', 'reconstruction/search-navigation/navigation.mjs', proof.admission.capture.source, proof.admission.parent.source, ...proof.contexts.map(({ factory }) => factory.source)];
    for (const name of paths) { const target = path.join(root, name); await mkdir(path.dirname(target), { recursive: true }); await copyFile(path.join(APP_ROOT, name), target); }
    assert.equal((await recover(root)).proof.moduleSha256, proof.moduleSha256);
    const target = path.join(root, proof.contexts[1].factory.source), bytes = await readFile(target); bytes[bytes.length - 1] ^= 1; await writeFile(target, bytes);
    await assert.rejects(recover(root), /capture authentication failed/);
  } finally { await rm(root, { recursive: true }); }
});
