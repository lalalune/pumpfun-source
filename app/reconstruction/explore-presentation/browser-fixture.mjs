// Authored standalone proof; source owner and host geometry are separate.
import * as React from 'react';
import * as jsx from 'react/jsx-runtime';
import * as compiler from 'react/compiler-runtime';
import { createRoot } from 'react-dom/client';
import { createExploreFixture } from './fixture.mjs';

const native = window.IntersectionObserver;
const observers = [];
class ObservedNative {
  constructor(callback, options) {
    this.record = { active: true, options, observed: [], callbacks: [] };
    observers.push(this.record);
    this.delegate = new native((entries, observer) => {
      this.record.callbacks.push(entries.map((entry) => ({ id: entry.target.id, isIntersecting: entry.isIntersecting, ratio: entry.intersectionRatio })));
      callback(entries, observer);
    }, options);
  }
  observe(element) { this.record.observed.push(element.id); this.delegate.observe(element); }
  unobserve(element) { this.delegate.unobserve(element); }
  disconnect() { this.record.active = false; this.delegate.disconnect(); }
}
const f = createExploreFixture({ React, jsx, compiler, window, document, IntersectionObserver: ObservedNative });
const root = createRoot(document.getElementById('root'));
let update;
let committed = 0;
let props = f.base;
function Story() {
  const [revision, setRevision] = React.useState(0);
  update = (patch = {}) => { props = { ...props, ...patch }; setRevision((value) => value + 1); };
  React.useLayoutEffect(() => { committed += 1; });
  return jsx.jsx(f.flow.PresentationFrame, { ...props, 'data-host-revision': revision });
}
root.render(jsx.jsx(Story, {}));
window.harness = {
  observe: () => ({ committed, observers, activeObservers: observers.filter(({ active }) => active).length,
    timers: f.calls.timers.size, observedPorts: [...f.calls.observed], hover: f.calls.hover, pages: f.calls.pages,
    retry: f.calls.retry, telemetry: f.calls.telemetry, cardProps: f.calls.cards.map((p) => ({ mint: p.coin.mint, name: p.coin.name, priority: p.priorityImage, eager: p.eagerLoadImage, viewport: p.isInViewport, bookmarked: p.isBookmarked, impression: p.impression })),
    visibility: f.calls.visibility, polling: f.calls.polling, lazyConstructors: f.calls.lazy.map(({ options }) => options) }),
  empty: () => update({ coins: [], feedError: false }),
  error: () => { f.state.variant = 'social-terminal'; update({ coins: [], feedError: true, searchTerm: '' }); },
  busy: () => update({ isLoading: true }),
  recover: () => update({ coins: f.base.coins, feedError: false, isLoading: false }),
  filters: () => update({ hasActiveFilters: true }),
  table: () => { f.state.layout = 'table'; update({ appliedFiltersKey: 'host-canonical-filter' }); },
  unmount: () => root.unmount(),
};
