# Captured callout image-preview owner

Actual callout/reply renderer **204478** invokes **364889.f** for reply, update
and selected main-image media. This recovers the complete 35-slot image owner,
including its refs/state, motion gate, natural-size calculation, scroll effect,
inline/host-link image and full popup descriptors. All three physical owner
variants are retained. Only the used **360827.V** style literal is included.
Video dispatch, composers, uploads and other callout actions stay outside.

The captured factory also bundles UI library **752365**. Its Root, Trigger,
Portal, Positioner and Popup are one shared instance: the verifier traces the
actual import, aliases and registration. That library is an **external port**;
its implementation is not copied, evaluated or claimed as newly recovered.
The selected owner itself is complete, rather than an isolated geometry helper.

## Explicit integration

```js
import { createCalloutImagePreview } from './client.mjs';
const ImagePreview = createCalloutImagePreview({
  jsx, jsxs, useMemoCache, React,
  HoverCard: sameInstanceHoverCardComponents,
  Link: callerSelectedLink,
  classNames: callerSelectedClassJoin,
  document: callerSelectedScrollEventTarget,
  window: callerSelectedViewport,
  Node: callerSelectedNodeRealm,
});
```

These are the source's actual JSX/compiler/React/class/Link/UI-library and DOM
interfaces. No provider, image service, routing or product mount is installed.
Only useRef/useState/useEffect, document scroll add/remove, window innerWidth/
innerHeight and the Node instanceof relationship are used from those ports.
Construct one stable component before mounting. Importing/constructing acquires
no cookie, storage, session or remote resource. The source remains an input-only
image renderer; the host controls the supplied src and whether any image loads.

## Source behavior

- Mouse entry clears the stored top coordinate. A mouse move whose native
  movementX or movementY differs from zero stores currentTarget's top. Opening
  for the exact reason `trigger-hover` is canceled when that stored coordinate
  differs from the current image ref's top. Other reasons bypass this gate.
- On an allowed open, the actual image's natural width/height and current
  viewport determine zoom dimensions. Bounds are min(90% viewport width,960)-8
  and min(85% viewport height,960)-8; scale is their fit ratio capped at 3 and
  output dimensions are rounded. Nonpositive image/bound sizes return null.
  The source adds no finite-value validator, so malformed NaN/Infinity values
  retain their original arithmetic behavior. Closing does not clear saved zoom.
- Only while open, the effect installs a capture/passive document scroll
  listener. It closes when the event target is an instance of the supplied Node
  realm and contains the image. An unrelated target leaves the preview open.
  The matching capture listener is removed on close or unmount.
- Priority selects eager/high versus lazy/undefined image hints. Density changes
  rounding. A truthy hostHref wraps the inline image in the supplied Link with
  prefetch false, tabIndex -1 and aria-hidden true; class placement changes with
  that wrapper. onHostClick remains a caller capability, not a new navigation.
- The popup retains exact side/align/offset/collision/class descriptors, test-ID
  derivation, preview-image decoding/draggable attributes and CSS zoom variables.
  The source supplies 600/100-ms trigger delays. These are descriptor values,
  not proof of the external library's actual timing/focus/portal/collision policy.

## Evidence and finite method

`verify.mjs` authenticates raw manifest/index registrations and UTF-16/UTF-8 byte
ranges, compares the complete owner across all three variants and regenerates
canonical editable source with explicit host bindings. Lossless tuple markers
retain array binding positions and arity in the existing lexical alpha comparator.
The three actual caller descriptors and their import remain source witnesses;
no parent action, image/video selector, provider or consumer lifecycle is inferred.
Captured bundles/factories are parsed as inert data, never imported/evaluated.

From `app/` with pinned dependencies already installed:

```sh
node reconstruction/callout-image-preview/verify.mjs --check
node --test tests/callout_image_preview.test.mjs tests/original_source.test.mjs
PUMP_IMAGE_PREVIEW_OUTPUT=/your/isolated/output node --test tests/callout_image_preview.browser.mjs
python3 scripts/verify-evidence.py
python3 scripts/progress.py --check
```

From the repository root:

```sh
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

The finite browser method uses real React/compiler/native DOM and a self-contained
data image. Its **authored provider host** delivers open-change reasons, clones
the actual trigger image and conditionally renders popup descriptors. It does
not implement or qualify 752365. Native movement, geometry and ancestor/unrelated
scrolls reach the reconstructed owner; unmount removes its actual listener.
The owned GET-only loopback fixture has no backend, Next server, external images,
router execution, credentials or network mutation. Retained outputs identify the
exact source/bundle inputs; qualification results apply only to those bytes.

No original UI-library/React/provider equivalence, live image availability,
product mount, visual/pixel/native/API/security parity, feature completion or
progress-count claim follows. Captures, prior packets, SDK and dependencies are
unchanged. Export/file names and host admission are local adaptation names;
original shipped code retains its authorship. Regenerate only after review with
`verify.mjs --write`.
