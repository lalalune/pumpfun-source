// Authored standalone React host; providers/translation/primitives are synthetic ports.
import * as React from 'react';
import * as jsxRuntime from 'react/jsx-runtime';
import { c as compiler } from 'react/compiler-runtime';
import { createRoot } from 'react-dom/client';
import { flushSync } from 'react-dom';
import { createAdvancedCreatorFeeControl } from '../client.mjs';

const el = React.createElement;
const subscribers = new Set(), quoteSubscribers = new Set(), translationSubscribers = new Set();
let state, initialState, quote = { pair: { kind: 'sol' } }, lastInputCallback, firstInputCallback;
const stateUpdates = [], translationCalls = [];
let language = 'A';
function translator(prefix) {
  return (key, variables) => {
    translationCalls.push({ prefix, key, variables });
    if (key === 'web.create.creator_fee_label') return `${prefix} Creator fee`;
    if (key === 'web.create.advanced') return `${prefix} Advanced`;
    if (key === 'web.create.creator_fee_placeholder') return `${prefix} range ${variables.min_percent} to ${variables.max_percent}`;
    if (key === 'web.create.creator_fee_invalid') return `${prefix} invalid ${variables.min_percent} to ${variables.max_percent}`;
    return key;
  };
}
let translation = { t: translator(language) };
function createBoundStore(initialize) {
  state = initialState = initialize((patch) => {
    stateUpdates.push(patch);
    state = { ...state, ...patch };
    for (const fn of subscribers) fn();
  });
  return (selector = (s) => s) => React.useSyncExternalStore(
    (notify) => { subscribers.add(notify); return () => subscribers.delete(notify); },
    () => selector(state), () => selector(initialState),
  );
}
function Input(props) {
  lastInputCallback = props.onChange;
  firstInputCallback ??= props.onChange;
  return el('input', props);
}
const runtime = createAdvancedCreatorFeeControl({
  createBoundStore,
  useQuoteState(selector) {
    return React.useSyncExternalStore(
      (notify) => { quoteSubscribers.add(notify); return () => quoteSubscribers.delete(notify); },
      () => selector(quote), () => selector(quote),
    );
  },
  useTranslation() {
    return React.useSyncExternalStore(
      (notify) => { translationSubscribers.add(notify); return () => translationSubscribers.delete(notify); },
      () => translation, () => translation,
    );
  },
  compiler, jsxRuntime, Input,
  Collapsible: {
    Y: ({ children, defaultOpen }) => el('section', { 'data-synthetic-default-open': String(defaultOpen) }, children),
    v: ({ children }) => children,
    C: ({ children, className }) => el('div', { className }, children),
  },
  Chevron: () => el('span', { 'aria-hidden': true }, '⌄'),
});
function Host() {
  return el('main', null,
    el('h1', null, 'Synthetic advanced-fee control host'),
    el('p', null, 'Selected source control with supplied state, quote, translation and primitives. No submit or fee projection.'),
    el(runtime.Control),
  );
}
let root = createRoot(document.getElementById('root'));
flushSync(() => root.render(el(Host)));
window.harness = {
  setQuote(kind) { quote = { pair: { kind } }; flushSync(() => { for (const fn of quoteSubscribers) fn(); }); },
  setLanguage(next) { language = next; translation = { t: translator(next) }; flushSync(() => { for (const fn of translationSubscribers) fn(); }); },
  setValue(value) { flushSync(() => state.setCreatorFeePercent(value)); },
  observe() { return { value: state.creatorFeePercent, quoteKind: quote.pair.kind, language,
    subscribers: subscribers.size, quoteSubscribers: quoteSubscribers.size, translationSubscribers: translationSubscribers.size,
    callbackSameAsFirst: lastInputCallback === firstInputCallback,
    updates: stateUpdates.map((v) => ({ ...v })), translationCalls: [...translationCalls] }; },
  unmount() { flushSync(() => root.unmount()); root = null; return this.observe(); },
};
