// Authored host: real React/compiler/DOM, synthetic provider/clock/scheduler.
import * as React from 'react';
import * as jsx from 'react/jsx-runtime';
import * as compiler from 'react/compiler-runtime';
import { createRoot } from 'react-dom/client';
import { createCoinCardFixture } from './fixture.mjs';
const f = createCoinCardFixture({ React, jsx, compiler });
const root = createRoot(document.getElementById('root'));
let update, committed = 0, showSecond = true;
function Story() {
  const [revision, setRevision] = React.useState(0);
  update = () => setRevision((value) => value + 1);
  React.useLayoutEffect(() => { committed += 1; });
  const second = { ...f.props, coin: { ...f.props.coin, mint: 'B', name: 'second coin' }, priorityImage: false };
  return jsx.jsxs(React.Fragment, { children: [
    jsx.jsx('div', { 'data-card-host': 'A', children: jsx.jsx(f.flow.Card, { ...f.props }) }, 'A'),
    showSecond && jsx.jsx('div', { 'data-card-host': 'B', children: jsx.jsx(f.flow.Card, second) }, 'B'),
    jsx.jsx('div', { id: 'cap-host', children: jsx.jsx(f.flow.MarketCap, { value: f.state.marketCap, transition: { duration: .2 } }) }),
    jsx.jsx('output', { id: 'host-revision', children: revision }),
  ] });
}
root.render(jsx.jsx(Story, {}));
window.harness = {
  observe: () => ({ committed, intervals: [...f.calls.intervals.values()].map(({ delay }) => ({ delay })), timeouts: f.calls.timeouts.size,
    clock: f.flow.clockSnapshot(), serverClock: f.flow.clockServerSnapshot(), query: f.calls.chartQuery, queryCommits: f.calls.queryCommits,
    creator: f.calls.creatorQuery, media: f.calls.media.map(({ coin, ...props }) => ({ mint: coin.mint, ...props })),
    avatars: f.calls.avatars, click: f.calls.click, routes: f.calls.routes, quote: f.calls.quote,
    lazyConstructors: f.calls.dynamic.map(({ options }) => options) }),
  flat: () => { f.state.points = [{ time: 1, price: 5 }, { time: 2, price: 5 }]; update(); },
  small: () => { f.state.marketCap = 100.5; update(); },
  large: () => { f.state.marketCap = 102; update(); },
  old: () => f.tick(1700007201000),
  dropSecond: () => { showSecond = false; update(); },
  unmount: () => root.unmount(),
};
