# Keep Settings open while Escape cancels input composition

Base: `abd766d7a8c047f14af34851f64166b840c6728d`. Its application tree is
byte-identical to the separately qualified `60bdd8a7` application baseline.

The Settings key handler dismissed the modal on every Escape, including a
trusted composing keydown. That interrupts conversion in the search input.
The [actual native/app comparison](before-pair.json) establishes the distinction:
under the same Chromium CDP `Input.imeSetComposition` and Escape sequence, both
keydown events are trusted and `isComposing: true`; a plain native dialog stays
open, while unchanged Settings closes and removes its query key. Both keyup
events report `isComposing: false`. The application probe recorded no page errors.

The five-line guard lets native composition cancellation run and stops the key
from reaching the underlying shell. It does not prevent the native default.
The existing non-composing Escape branch is unchanged. A subsequent ordinary
Escape still dismisses Settings while preserving the sidebar and Live state.

This is a defect fix in the local reconstructed UI. The native HTML control is
a platform reference, not a captured original Pump interaction. No original
product parity, OS-level IME matrix, other-browser, backend, authentication or
feature-completion claim is made. Original captures, SDK source, preference
behavior and shared shell handlers are unchanged.

## Evidence and checks

- [Actual baseline failure](before.log.gz): the new 390px browser case proves a
  trusted composing keydown, then fails because Settings disappears. The gzip
  preserves the raw log, including reporter whitespace. The test source is
  identical before and after the fix.
- [Final browser run](final-browser.log): **18 pass** — two new trusted-input
  cases at 390/1280px plus all 16 maintained Settings cases. The new cases check
  focus, allowed native default, the next ordinary Escape, URL preservation,
  mobile-sidebar preservation and the actual Live playback boundary.
- [Before mobile](before-mobile.png), [after mobile](after-390.png) and
  [after desktop](after-1280.png) are local screenshots, visually inspected.
  The mobile before/after use the same 390×844 viewport and action sequence.
- Frontend TypeScript check, ten Settings model tests, three source-contract
  tests and evidence verification (698 objects, npm integrity, unchanged SDK)
  pass. A new production build is not claimed.

From `/app`, using the existing pinned dependencies and Chromium:

```sh
pnpm --filter @pump-reconstruction/frontend exec playwright test tests/settings-ime.spec.ts tests/settings.spec.ts --max-failures=1
pnpm --filter @pump-reconstruction/frontend typecheck
node --experimental-strip-types --test tests/settings_model.test.ts
node --test tests/settings-contract.test.mjs
python3 scripts/verify-evidence.py
```

The executed browser run used the same defaults and an already-running local
Next server on port 3010; its temporary config omitted `webServer`. The initial
baseline and two-case candidate run used port 3027. Next 16.4.1, Playwright
1.64.1, TypeScript 5.9.3, Node 24.19.0 and Chromium 156.0.8078.4 were used.

[probe.mjs](probe.mjs) preserves the actual observational producer byte-for-byte.
Its workspace and output paths describe this run; replaying it at another
checkout requires adjusting that path constant. The maintained Playwright
regressions above use the repository's normal portable configuration. Neither
producer executes captured JavaScript or sends production mutations.
Hashes and command results are recorded in [SOURCE.json](SOURCE.json).
