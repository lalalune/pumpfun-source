# Reveal the selected Settings tab

Base: `60bdd8a7a522921058d18563bb9335d2a06aec75`.

Opening `/?settings=privacy&setting=privacy.confirmExternalLinks` at 390px
focuses the Privacy setting, but the selected Privacy tab is entirely outside
the horizontal tab rail. The real Chromium regression fails on the unmodified
base because the selected tab's bounding rectangle is outside the rail's client
rectangle. [Before](before-mobile.png) and [after](after-390.png) use the same
390×900 viewport and deep link; [desktop](after-1440.png) is 1440×900. These are
local reconstruction screenshots, not original website reference captures.

The fix adjusts only the rail's `scrollLeft` when the selected tab crosses an
edge. It runs on opening/section changes and observes the rail's size so a
desktop-to-mobile resize also reveals the active tab. It does not focus the
tab or scroll the document. The observer disconnects when that effect ends.
Existing dialog dismissal, body-scroll ownership and preference behavior are
unchanged.

The captured Settings factory `124884-dfcb487f79e6` renders section tabs through
`439587-556a5e98fc38`. That confirms the tab structure, not this scrolling
algorithm. This is a reproduced local UI defect fix; no original interaction
equivalence, backend implementation, authentication or feature-completion credit
is claimed. Existing source/evidence contracts and captured bytes are unchanged.

## Checks

- [Unmodified-base browser failure](before.log.gz): the hydrated setting is focused,
  but the selected tab fails the rail-bounds assertion at 390px. The gzip retains
  the exact raw log bytes, including the reporter's trailing whitespace.
- [Final browser run](final-browser.log): **21 pass**. Five new cases cover
  320/390/1440px deep links, URL selection in an already-open Live dialog, and
  desktop-to-mobile resizing followed by selecting the first tab. The unchanged
  16 Settings cases also pass, including Escape, Back, focus, nested sidebar,
  viewport bounds and the no-service-write/permission case.
- All 10 Settings model tests and 3 source-contract tests pass.
- Application evidence verifier passes all 698 objects, npm integrity and
  unchanged SDK sources. `git diff --check` passes.
- Frontend typecheck fails on the same unrelated base error:
  `src/app/holder-rewards-config/server.ts:77`, `unknown` is not assignable to
  `PublicKeyInitData`. [Actual output](typecheck.log). No unrelated cast or source
  repair is included. No full production build is claimed.

Reproduce from `/app` with the existing installed dependencies and Chromium:

```sh
pnpm --filter @pump-reconstruction/frontend exec playwright test tests/settings-tab-visibility.spec.ts tests/settings.spec.ts --max-failures=1
node --experimental-strip-types --test tests/settings_model.test.ts
node --test tests/settings-contract.test.mjs
python3 scripts/verify-evidence.py
pnpm --filter @pump-reconstruction/frontend typecheck
```

The final run used the same Playwright defaults with an already-started local
Next server on port 3010; its temporary config omitted `webServer`. The earlier
five-case pass used port 3027. Versions: Node 24.19.0, Next 16.4.1, Playwright
1.64.1. The tests do not click or focus the selected tab before measuring it,
because that would let native focus scrolling hide the defect. URL changes use
the documented `replaceState(null, ...)` integration after a real controlled
interaction, not Next's reserved internal history state.

Setup failures are preserved privately and are not counted as product failures:
an accidentally created empty `frontend/app` directory caused an initial 404
until removal/restart; copying reserved Next history state prevented the first
URL-transition fixture from updating; missing sparse-checkout capture files
made the first broader run fail closed on Live. All evidence paths were then
authenticated to base Git blobs and linked read-only. The final 21-case run uses
those authentic files and unchanged existing tests. The original bounds failure
is separate from these setup failures. File hashes are in [SOURCE.json](SOURCE.json).
