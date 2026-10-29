// Authored standalone host. All query, picker, state facades and art primitives are synthetic ports.
import * as React from 'react';
import * as jsxRuntime from 'react/jsx-runtime';
import { c as compiler } from 'react/compiler-runtime';
import { createRoot } from 'react-dom/client';
import { flushSync } from 'react-dom';
import { createQuoteSelectionCoordinator } from '../client.mjs';

const el = React.createElement, quoteSubscribers = new Set(), readerSubscribers = new Set(), translationSubscribers = new Set();
const stock = { mint: 'synthetic-stock', symbol: 'Stock name', ticker: 'STK', nested: { retained: true } };
const pump = { mint: 'synthetic-pump', name: 'Pump name', symbol: 'PMP', nested: { retained: true }, untouched: 12 };
const missingPump = { mint: 'synthetic-missing', name: null, nested: pump.nested, untouched: 19 };
const emptyPump = { mint: 'synthetic-empty', name: '', symbol: '', untouched: 20 };
let state, initialState, query = { data: [], isPending: false }, language = 'A', pickerProps;
const calls = [], translations = [];
const mayhem = { isMayhemEnabled: false, setIsMayhemEnabled(value) { calls.push(['mayhem', value]); this.isMayhemEnabled = value; } };
const sharing = { enabled: false, setEnabled(value) { calls.push(['sharing', value]); this.enabled = value; } };
function translator(prefix) {
  return (key, variables) => {
    translations.push({ prefix, key, variables });
    if (key === 'web.create.pair_asset_label') return `${prefix} Pair asset`;
    if (key === 'web.create.pair_stocks') return `${prefix} Stock / Pump`;
    if (key === 'web.create.pair_select_stock') return `${prefix} Select asset`;
    if (key === 'web.create.pair_with_stock') return `${prefix} Pair ${variables.symbol} / ${variables.ticker}`;
    if (key === 'web.create.pair_change') return `${prefix} Change`;
    return `${prefix}:${key}`;
  };
}
let translation = { t: translator(language) };
function createBoundStore(initialize) {
  state = initialState = initialize((patch) => {
    calls.push(['quote', patch]); state = { ...state, ...patch };
    for (const notify of quoteSubscribers) notify();
  });
  return (selector = (s) => s) => React.useSyncExternalStore(
    (notify) => { quoteSubscribers.add(notify); return () => quoteSubscribers.delete(notify); },
    () => selector(state), () => selector(initialState),
  );
}
function PickerBody(props) {
  pickerProps = props;
  return el('div', { 'data-testid': 'picker-body' },
    el('p', null, 'Synthetic picker port: emits supplied records only. No search or eligibility implementation.'),
    el('output', { 'data-testid': 'picker-loading' }, String(props.isLoading)),
    el('output', { 'data-testid': 'picker-count' }, String(props.stocks.length)),
    el('button', { type: 'button', disabled: !props.stocks[0], onClick: () => props.onSelect(props.stocks[0]) }, 'Emit stock callback'),
    el('button', { type: 'button', onClick: () => props.onSelectPumpCoin(pump) }, 'Emit Pump callback'),
    el('button', { type: 'button', onClick: () => props.onSelectPumpCoin(missingPump) }, 'Emit missing-name callback'),
    el('button', { type: 'button', onClick: () => props.onSelectPumpCoin(emptyPump) }, 'Emit empty-name callback'),
    el('button', { type: 'button', onClick: props.onClose }, 'Close supplied picker'),
  );
}
const runtime = createQuoteSelectionCoordinator({
  createBoundStore, React, compiler, jsxRuntime,
  useTranslation: () => React.useSyncExternalStore(
    (notify) => { translationSubscribers.add(notify); return () => translationSubscribers.delete(notify); },
    () => translation, () => translation,
  ),
  useStocks: () => React.useSyncExternalStore(
    (notify) => { readerSubscribers.add(notify); return () => readerSubscribers.delete(notify); },
    () => query, () => query,
  ),
  mayhemState: { getState() { calls.push(['mayhem-read']); return mayhem; } },
  feeSharingState: { getState() { calls.push(['sharing-read']); return sharing; } },
  toast: { info(message) { calls.push(['info', message]); } }, classes: (...values) => values.join(' '),
  Image: ({ src }) => el('span', { 'aria-hidden': true, 'data-supplied-image': src }, '◇'),
  StockArt: () => el('span', { 'aria-hidden': true }, '□'),
  CoinAvatar: () => el('span', { 'aria-hidden': true }, '○'),
  Chevron: () => el('span', { 'aria-hidden': true }, '⌄'),
  Dialog: ({ isOpen, onIsOpenChange, children }) => isOpen ? el('div', { role: 'dialog', 'aria-label': 'Synthetic picker gateway' },
    el('button', { type: 'button', onClick: () => onIsOpenChange(true) }, 'Emit open notification'),
    el('button', { type: 'button', onClick: () => onIsOpenChange(false) }, 'Emit close notification'), children) : null,
  DialogContent: ({ children, className }) => el('div', { className }, children), PickerBody,
});
function Host() {
  return el('main', null, el('h1', null, 'Synthetic Create quote coordinator'),
    el('p', null, 'Source coordinator with supplied quote/query/flags/dialog/picker/art ports. No wallet, service or submission.'),
    el(runtime.Control));
}
let root = createRoot(document.getElementById('root'));
flushSync(() => root.render(el(Host)));
function observe() {
  const pair = state.pair;
  return { pair, isQuoteMintEnabled: state.isQuoteMintEnabled,
    mayhem: mayhem.isMayhemEnabled, sharing: sharing.enabled, calls: [...calls], language,
    sameStockReference: pair.stock === stock,
    samePumpReference: pair.coin === pump, samePumpNestedReference: pair.coin?.nested === pump.nested,
    pickerFields: pickerProps ? Object.keys(pickerProps) : [],
    pickerSameReaderArray: pickerProps?.stocks === query.data,
    quoteSubscribers: quoteSubscribers.size, readerSubscribers: readerSubscribers.size, translationSubscribers: translationSubscribers.size,
    translations: [...translations] };
}
window.harness = {
  observe,
  supplyStocks(mode = 'loaded', pending = false) { query = { data: mode === 'loaded' ? [stock] : mode === 'null' ? null : undefined, isPending: pending }; flushSync(() => { for (const fn of readerSubscribers) fn(); }); },
  flags(a, b) { mayhem.isMayhemEnabled = a; sharing.enabled = b; },
  clearCalls() { calls.length = 0; },
  setQuote(pair) { flushSync(() => state.setPair(pair)); },
  setLanguage(next) { language = next; translation = { t: translator(next) }; flushSync(() => { for (const fn of translationSubscribers) fn(); }); },
  unmount() { flushSync(() => root.unmount()); root = null; return observe(); },
};
