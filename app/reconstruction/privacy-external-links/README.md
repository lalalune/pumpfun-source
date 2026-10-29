# Original external-link confirmation preference

This recovers a backend-free **device preference** and its actual outbound-link consumer. It provides a maintained fixed-key preference runtime, an explicitly injected confirmation controller, reproducible source contract, isolated browser/state checks, and a working device switch in the existing Settings privacy row. The shared shell and modal dismissal behavior remain unchanged; no native server, auth, production navigation or visual-parity claim is added.

The captured chain is **956718**'s `privacy.confirmExternalLinks` descriptor → **654506** JSON storage adapter → **547562** setting hook / **272700** registry → **225641** outbound confirmation → **634557** actual link consumer. **402732** is the `WEB_SETTINGS_HUB` gate. **671027** supplies initialization; this selected descriptor has no legacy adoption list. All **four** outbound-hook variants and **three** consumer variants are retained explicitly, without choosing an active page winner. Other registry settings are not implemented.

The AST-only verifier authenticates physical registration, original/factory hashes and strict UTF-16/UTF-8 witnesses, checks complete selected helper/variant syntax and actual import/caller/descriptor edges, and retains every available direct import variant in the 5,947-variant inventory. Captured JavaScript is never executed/imported.

## Recovered preference

- Scope is **device**, key `privacy.confirm-external-links`, codec JSON, default `true`. Only a decoded strict `false` disables confirmation. A missing or malformed value and all other decoded values enable it. This is a client descriptor/default, not a server default or account ownership policy.
- A successful write stores JSON and clears the runtime fallback. A failed write retains a shared in-memory fallback and still notifies subscribers. That fallback is not durable, and an external storage event does not clear it. A new module/runtime lifetime reads persisted storage instead.
- Removal swallows storage errors, clears the parsed/fallback caches and notifies. It cannot fabricate deletion: if removal failed, the next read may return the old persisted value.
- `storage` and `local-storage` listeners install lazily. Exact-key events and null/undefined-key clear events notify the selected preference; other keys do not. Subscriber cleanup removes that callback, including the original Set deduplication behavior. The module-lifetime listeners remain installed. Multiple `preference()` consumers from one runtime share caches/fallback/subscribers.

`privacyPreferenceRuntime` models this selected key within one original module lifetime. It is not a generic clone of the entire settings framework, functional-updater API, SSR/hydration or unrelated registry/legacy settings.

## Recovered outbound decisions

Input is trimmed; protocol-relative input gains `https:`, and a non-HTTP(S) prefix gains `https://`. The parsed URL must be HTTPS. Empty/invalid input returns null. Trusted-host comparison removes one `www.` prefix, then checks exactly the three captured hosts. The historical list is client behavior, not a security clearance or implementation of any excluded destination.

The confirmation condition is `!WEB_SETTINGS_HUB || preference`. Trusted links bypass it. When the hub is disabled, an untrusted link still prompts even if storage contains false, and the remembered-choice checkbox is unavailable. A prompted request resets that checkbox and stores its normalized pending URL.

Confirming a pending URL writes false **only** when the hub is enabled and the checkbox is true, before the open call. It then closes and clears the URL. Cancel closes/clears the URL; the next prompted request resets the checkbox. Invalid or directly opened requests do not silently clear an already pending dialog. The source ignores the popup's return value; no navigation-success acknowledgement is invented. A thrown open/write port error can prevent later cleanup, as the original sequence does.

The actual link consumer prevents default and stops propagation before its optional caller callback and navigation request. Invalid normalized links render as a disabled-looking span in the source. This controller does not recreate that component's styling or React rendering: it models settled state and explicit integration ports, with arbitrary reentrant/React scheduling behavior outside the claim.

## Explicit integration

```js
import { privacyPreferenceRuntime, outboundConfirmation } from "./client.mjs";

const runtime = privacyPreferenceRuntime({
  getStorage: () => window.localStorage,
  events: window,
  createStorageEvent: (type, init) => new StorageEvent(type, init),
});
const preference = runtime.preference();
const controller = outboundConfirmation({
  preference,
  settingsHubEnabled: originalSettingsHubFlag,
  openWindow: explicitWindowOpenPort,
});
controller.requestNavigation(selectedHref);
// A renderer uses getSnapshot/subscribe, setDontAskAgain, confirm and cancel.
// On unmount, remove this controller's preference subscription:
controller.dispose();
```

Importing the module has no side effects. Constructing/using these explicit ports reads only the selected device key and subscribes as described. No implicit window-open, storage, flag service, credentials, browser permission, analytics or network implementation is supplied. The controller's observer/input API is local integration design, not a recovered server API or a claim about React interleavings.

## Settings UI

Open Settings → Privacy, or `/?settings=privacy&setting=privacy.confirmExternalLinks`. The switch uses this same fixed-key runtime through `useSyncExternalStore`, with a server snapshot and disabled loading state before hydration. It stores a device preference shared across accounts; it does not require a signed-in wallet. Only this previously unavailable row gains a control. Other account values remain unavailable unless the existing explicit notification adapter supplies them.

The UI checks storage after a write before reporting “Saved in this browser.” A failed or unconfirmed write retains the original page-lifetime fallback and displays a warning; reload can restore the persisted choice. No server or browser-permission request is involved. The renderer and persistence feedback are authored integration, not a recovered pixel layout.

Create draft preview links reuse this controller and the same device preference instance. The local shell supplies `settingsHubEnabled: true` because its Settings switch is available; no upstream flag rollout is inferred. See [`CREATE-EXTERNAL-LINKS.md`](../../packages/frontend/CREATE-EXTERNAL-LINKS.md) for that separate consumer. Normal interactive site-footer clicks now use the same local capability through a persistent footer host, including portal-menu items. Other app links remain unconnected; the native anchor attributes are preserved. The existing clickwrap overlay blocks the JavaScript-disabled full-page interaction, so no usable no-JS application workflow is claimed. This is confirmation UX, not an authorization or security guarantee.

The original `app-browser/` receipt, producer and screenshots remain unchanged historical switch-only evidence (`outboundConsumersExercised: false`). They do not qualify the changed control or footer. The current `--check-app-browser` gate explicitly selects [`research/footer-link-confirmation-20261029/browser`](../../research/footer-link-confirmation-20261029/browser), binds its current control/consumer/test sources and checks the new workflow receipt; old hashes are not rewritten.

## Verify

```sh
node app/scripts/original-privacy-external-links.mjs --check --check-browser --check-app-browser
node --test app/tests/original_privacy_external_links.test.mjs app/tests/original_source.test.mjs
python3 app/scripts/verify-evidence.py
# Rerun the authored isolated browser workflow with existing frontend Playwright:
node app/tests/original_privacy_external_links.browser.mjs \
  --output app/reconstruction/privacy-external-links/browser-verification.json
# With the actual frontend started separately on a loopback port:
node app/tests/footer_privacy.browser.mjs \
  --base-url http://127.0.0.1:3027 \
  --output app/research/footer-link-confirmation-20261029/browser/verification.json
```

`--write` regenerates only the source-derived contract. `--check-browser` checks the isolated harness receipt; `--check-app-browser` checks the selected current Settings/footer workflow receipt, exact renderer/consumer/runtime/script/contract inputs and desktop/mobile screenshot hashes. Neither reruns a browser or makes a receipt an independent oracle. Source or browser-module changes require renewed qualification, not just rewritten hashes. The shared `settings-control.tsx` host is the one exception: its receipt hash records the exact bytes the browser run used, and the check only requires the current host to keep mounting `PrivacySettingControl` for `privacy.confirmExternalLinks`; the receipt does not qualify later host edits.

The Node tests cover coercion, failure fallback, failed removal, shared lifetime, subscriptions, exact URL/host behavior, hub gates, pending-dialog state, ordering and errors. Resealed source mutations, missing variants and invented durability/account claims fail. Receipt mutations and changes after execution also fail.

The browser harness is authored synthetic test UI, not a captured-settings reconstruction. It uses an isolated temporary Chromium profile and real WebStorage/StorageEvents: explicit confirmation and JSON persistence, a **full browser-process restart**, a second page's native cross-tab storage event, and desktop/mobile viewport cancel/flag cases. Its explicit open port records arguments; no destination is opened. The checked-in receipt binds the actual executed bytes and reports no page errors or external requests. This is finite client workflow evidence, not popup behavior, product visual parity, current upstream availability or backend compatibility.

### Historical switch-only qualification

The retained `original_privacy_settings.browser.mjs` driver opens the existing Settings modal, operates the real switch with a keyboard, verifies persistence on reload and full browser-process restart, observes a native cross-tab update, and checks a targeted storage-write failure at a mobile viewport. It preserves unrelated browser data and binds desktop/mobile screenshots. The failure is injected only into the selected key's `Storage.setItem` in the isolated test browser; no production failure or server oracle is claimed. The actual browser workflow must be run before its receipt is accepted.

The unchanged historical `app-browser/` receipt passes all four checks with zero page errors/external requests. Strict frontend typechecking and all 29 affected/shared-source Node tests pass. An additional run of the existing 15-case Settings suite stopped after three passes and a Back-dismissal failure (11 cases not run). The same Back case failed after temporarily restoring the exact pre-UI `SettingsControl` on the same server; the qualified privacy source was then restored byte-for-byte. `app-browser/additional-regression.json` and `baseline-back-failure.md` preserve this limit. This is not a full Settings-suite pass or a claim that history behavior was repaired. Initial working-directory/config invocation errors occurred before test execution and are disclosed separately in that record.

### Current footer qualification

The selected current receipt records seven interactive workflows and one server-rendered anchor-attribute check. It covers cancellation/focus, remembered choice and reload, portal-menu teardown, mobile links, throwing-open recovery with a native anchor, failed persistence feedback and shared behavior with unchanged Create preview links. Opening is an explicit test port; the one native fallback receives a synthetic browser response without contacting the destination. The old no-JavaScript activation attempt was blocked by the existing clickwrap overlay and is retained as a limitation, not an activation success. See the [footer integration packet](../../research/footer-link-confirmation-20261029/README.md) for the same-method base failure and executed checks.

Original captures, inventory, SDK/dependencies/lock, feature ledger and paused local backend prototype remain unchanged. The integration changes only the footer host and truthful setting scope copy; shared modal behavior, global styles, clickwrap, DropdownMenu and Create preview source stay unchanged. No app-wide link policy, backend compatibility, security guarantee or original flag rollout is inferred.
