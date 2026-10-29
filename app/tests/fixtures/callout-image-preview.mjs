import React, { useEffect, useState } from '../../packages/frontend/node_modules/react/index.js';
import { createRoot } from '../../packages/frontend/node_modules/react-dom/client.js';
import { c as useMemoCache } from '../../packages/frontend/node_modules/react/compiler-runtime.js';
import { jsx, jsxs } from '../../packages/frontend/node_modules/react/jsx-runtime.js';
import { createCalloutImagePreview } from '../../reconstruction/callout-image-preview/client.mjs';

// Authored provider host only. This does not implement captured752365 or routing.
const image = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100"><rect width="200" height="100" fill="teal"/></svg>');
const context = React.createContext(null), events = [], active = new Set();
let currentRoot, root, setProps, setShift, serial = 0, hostClicks = 0;
document.addEventListener('scroll', (e) => events.push({ type: 'observed-native-scroll', targetId: e.target.id ?? '' }), { capture: true, passive: true });
const documentPort = {
  addEventListener(type, listener, options) {
    events.push({ type: 'source-listen', event: type, options }); active.add(listener);
    document.addEventListener(type, listener, options);
  },
  removeEventListener(type, listener, options) {
    events.push({ type: 'source-unlisten', event: type, options, known: active.has(listener) }); active.delete(listener);
    document.removeEventListener(type, listener, options);
  },
};
const HoverCard = {
  Root({ children, ...value }) {
    useEffect(() => { currentRoot = value; serial++; });
    return jsx(context.Provider, { value, children });
  },
  Trigger({ render, onMouseEnter, onMouseMove, delay, closeDelay }) {
    return React.cloneElement(render, {
      onMouseEnter(e) { events.push({ type: 'native-image-enter', delay, closeDelay }); onMouseEnter(e); },
      onMouseMove(e) { events.push({ type: 'native-image-move', x: e.nativeEvent.movementX, y: e.nativeEvent.movementY, top: e.currentTarget.getBoundingClientRect().top }); onMouseMove(e); },
    });
  },
  Portal: ({ children }) => children,
  Positioner: ({ children, side, align, sideOffset, collisionPadding, ...props }) => jsx('div', { ...props, 'data-authored-positioner': [side, align, sideOffset, collisionPadding].join(':'), children }),
  Popup(props) { return React.useContext(context).open ? jsx('div', props) : null; },
};
const Preview = createCalloutImagePreview({ jsx, jsxs, useMemoCache, React, HoverCard,
  Link({ children, prefetch, onClick, ...props }) {
    return jsx('a', { ...props, 'data-authored-prefetch': String(prefetch), onClick(e) { e.preventDefault(); onClick?.(e); }, children });
  },
  classNames: (...xs) => xs.filter(Boolean).join(' '), document: documentPort, window, Node,
});
function App({ initial }) {
  const [props, update] = useState(initial), [shift, updateShift] = useState(0);
  setProps = update; setShift = updateShift;
  return jsx('div', { style: { paddingTop: shift }, children: jsx(Preview, {
    src: image, testId: 'source-image', className: 'authored-extra-class',
    onHostClick: () => { hostClicks++; }, ...props,
  }) });
}
function mount(initial = {}) { currentRoot = undefined; root = createRoot(document.getElementById('root')); root.render(jsx(App, { initial })); }
window.imagePreviewHarness = {
  mount,
  state: () => ({ ready: !!currentRoot, open: currentRoot?.open ?? false, serial, listeners: active.size, hostClicks, events: structuredClone(events) }),
  shift: (value) => setShift(value),
  props: (patch) => setProps((old) => ({ ...old, ...patch })),
  requestOpen(value, reason) {
    let canceled = false; const event = { reason, cancel() { canceled = true; events.push({ type: 'source-cancel', reason }); } };
    currentRoot.onOpenChange(value, event); return { canceled };
  },
  unmount() { root.unmount(); currentRoot = undefined; },
};
mount();
