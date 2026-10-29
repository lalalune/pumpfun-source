# Main `/live` outer preview and carousel controller

This editable source adaptation closes the main-page **369731 HeroCarousel →
selected HeroSlide → 41705 preview/media handoff**. It preserves the complete
selected components and local callbacks, including their compiler memo-cache
slots. It does not implement the actual media player, services or provider.

The authenticated `https://pump.fun/live` HTML contains Flight import **116** for
**31113 LiveHomepage**, used by the nested element in record **7f**. That caller
passes its initial hero data through **133244._ → 859960.L → 369731**. The selected
parent/hero/preview scripts occur in the captured initial HTML. This is an actual
main-page source context, not a coin-detail player reconstruction. The old six
records establish context only; they are not replayed in the new behavior tests.

Related open #1570/#1617 reconstruct archived category/hero metadata and selection;
open #1821 reconstructs listing data. They are credited related work, not imports
or prerequisites of this unit. Captures and the shared source reader/Flight parser
are already in main `094a06f18df738d41e77070c1a009e135671ac1a`.

## Complete recovered outer behavior

- Looping next/previous state, nonlooping clamp logic, count-shrink effect,
  selected-index setter and selected/inactive-slot rendering. An inactive slot
  captures a click, prevents its default and propagation, then selects the slot.
  Source spread precedence is retained: stream fields follow `isSelected`.
- Actual ResizeObserver/MutationObserver card-width measurement and cleanup,
  selected-index scroll effect, skip/loop scroll behavior and scrollend rounding
  callback. Browser/layout/snap scheduling remains the host's behavior.
- The original shared HeroSlide mute provider, per-scope toggle/fallback,
  autoplay-failure callback and subsequent document click/keydown gesture gate.
  This recovers outer control visibility, not a media retry policy or a guarantee
  that a real player starts/mutes/recovers.
- Only selected/hover-active previews mount. The preview's ready callback calls
  its optional parent callback before setting its local ready state. The loading
  prop is the inverse of that state. Selection does **not** require a playlist;
  an undefined URL remains an input to the unimplemented player capability.
- Complete updated-thumbnail/IPFS choice, thumbnail-load/error visibility state,
  original caller override precedence and media props, including mute, creator,
  live flag, loader type and disabled hover/visibility playback flags.
- Complete stage, pagination dots, HeroSlide metadata/description and mute-button
  components. Unrelated badge/metadata widgets, navigation/prefetch, telemetry and
  account/trade CTA components are explicit ports; their internals are not copied.

## Capability interface

```js
import { createLivePreviewFlow } from './components.mjs';
const { HeroCarousel, VideoMuteProvider } = createLivePreviewFlow({
  React, jsx, compiler: { c: useMemoCache },
  modules: callerProvidedModules,
  loadPreview: callerProvidedPreviewLoader,
  dom: { document, ResizeObserver, MutationObserver },
});
// Render React.createElement(VideoMuteProvider, {},
//   React.createElement(HeroCarousel, {livestreams})) in the host.
```

`modules` binds the actual imported capabilities identified by numeric ID in
`PROVENANCE.json`. The adapter supplies its recovered modules internally. All
remaining imports are mandatory explicit module values: icon/UI components,
translation, URI/class helpers, metadata/provider wrappers, prefetch, navigation,
telemetry and the dynamic-component adapter. There is no production endpoint,
network, default module resolver or credential store.

The actual source lazy loader is **47367 → 971491 → 773918
LivestreamPreviewPlayer**. The adapter changes only `runtime.A(47367)` to the
explicit `loadPreview(47367)` capability; its original dynamic options remain.
The full real player factory and **202541** provider-switch factory are
authenticated as excluded boundaries. Their auth/token/join/presence/provider/HLS
behavior is neither loaded nor executed. The outer provider receives its original
flags, including `shouldJoinChatRoom`; recording that handoff is not implementing
or authorizing a join. No individual coin page is implemented or visited.

The host adapter constructs these modules once. It does not reproduce the
original module registry, active-registration order, import cache, dynamic-loader
scheduling, stylesheet injection or complete application provider tree. UI ports
must be supplied explicitly; the module is not mounted in the maintained app.

## Source verification and finite proof

From `app/`, with the existing pinned dependencies:

```sh
node reconstruction/live-preview-flow/recover.mjs --check
node --test tests/live_preview_flow.test.mjs
node reconstruction/live-preview-flow/browser.mjs --output NEW_OUTPUT_DIRECTORY
python3 scripts/verify-evidence.py
python3 scripts/progress.py --check
```

The generator parses authenticated raw factories without evaluating/importing
them. It preserves selected declarations and complete component bodies, replacing
only module imports/exports, the one preview-loader call and explicit DOM globals.
The check reconstructs the entire editable output and compares exact bytes, then
checks the provenance document. A changed clamp, missing grouped context and
rehashed changed Flight component fail. Public-input export needs no private
workfiles or formatted-module fallback. Use `--write` only for reviewed regeneration.

The standalone browser harness uses real React 19.2.3/compiler/DOM/observers with
explicit synthetic player, image, navigation, metadata-provider and telemetry
ports. It uses the existing #1846 standalone esbuild/Playwright infrastructure
approach. Synthetic controls deliver readiness/failure callbacks; no original
media, service, playlist, coin navigation or socket is requested. Its CSS is only
test geometry, not an original screenshot/layout qualification.

The source proof has **12 physical factory contexts, 96 selected-source
witnesses, nine explicit parent/import-use edges and seven authenticated lazy
assets**. The five new source/portable/mutation checks and eleven unchanged
shared-reader checks pass.

The browser evidence is deliberately split: **d3297e15 cases 1–2 pass** and
**c0572712 cases 3–6 pass**, covering six distinct interactions. There is no
all-six pass at the final head. The initial off-screen-target attempt failed its
capture-only expectation; the next attempt failed its click-coupled synthetic
autoplay-failure expectation. Both failure traces, screenshots, methods and clean
shutdown records remain in [qualification](./qualification/README.md). The final
continuation adds an out-of-click synthetic failure capability, then observes a
subsequent real key gesture. No original media-autoplay scheduling is inferred.
The two earlier passing assertion bodies and all recovered component bytes are
unchanged; exact method/source mappings explain their limited applicability.
Observer/listener cleanup bodies are source-bound. Runtime directly observes
synthetic-player unmount and host/browser shutdown, without per-listener counts.

No current-live truth, media acquisition/playback, auth/LiveKit/presence, service
compatibility, native feature milestone, whole-runtime equivalence, original
visual parity or security approval is claimed. Existing captures, source packets,
SDK, application pages and progress ledgers remain unchanged. Original shipped
JavaScript retains its authorship; descriptive wrapper/export names are local.
