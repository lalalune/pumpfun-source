# Recent-query history in the maintained search dialog

The captured SearchDialog records submitted terms in `recently-searched-terms`,
but the maintained shell lost searches on reload and had no history controls.
This fills that client workflow with real browser-owned input records. It
does not add a service or populate market/profile data.

The used add callback removes every strict-equal occurrence of the submitted
term, keeps the next 19 entries and prepends the term. Case and spacing are
preserved by that operation; the actual form caller trims its nonempty input
before recording. The callback retains one render's term snapshot. Clear
writes a fresh empty array, rather than removing the key or clearing other
browser data. The text-query destination uses encodeURIComponent, and clicking
an existing history link does not promote it.

The current UI reads after mount, records actual nonempty form submissions,
shows the first three terms when the raw input is empty, follows text-query
links and exposes Clear. Whitespace input hides the history, matching the
captured raw-query condition. The original expanded list depends on a feature
flag; this unit presents only the collapsed branch and infers no flag default.
Stored strings remain query text here. Coin/user/squad enrichment and their
navigation/classification are outside this unit.

The add/clear/href bodies are compared as complete lexical ASTs against their
actual used 238128 callbacks. The actual hook tuple, storage key/default,
trimmed submit call, history render/clear/navigation/visibility consumers and
536925.j storage dependency are authenticated from raw capture registrations.
`PROVENANCE.json` retains URLs, hashes and UTF-16/UTF-8 ranges. The existing
planner comparator is reused unchanged, without new infrastructure credit.
Captured JavaScript is parsed, never evaluated or imported. Descriptive names
and the TypeScript interfaces are local reconstruction choices; upstream code
retains its authorship. The prior submit/navigation work remains separate.

Persistence is local integration around those operations. A storage write
precedes state publication and the same-tab notification; native same-origin
storage events update another page. Reads subscribe/clean up both original
event names. The typed local decoder accepts renderable string arrays and
preserves their values. Malformed JSON, wrong types, invalid URI text and
browser storage failures show unavailable state without automatic deletion.
Clear can explicitly reset that key. A failed history write permits the
existing form navigation to proceed. These user-facing errors and typed
validation are local choices, not original general-hook diagnostic identity.
React scheduling, arbitrary JSON deserialization and full hook equivalence
remain unqualified; no cross-tab write serialization is promised.

The preserved historical trial used the frozen main31cea320 cohort. There, the new browser regression fails at the
missing history region after two actual submissions and reload. With
max-failures1 it stops there: the other four new cases did not run on the base.
That historical candidate passes all five plus two existing shell cases, seven
total. These cover reload/link order and encoding, raw visibility, strict
dedup/cap20/collapsed3/clear scope, malformed data recovery, quota-failed-write
navigation and real cross-page storage events. The observer only notes actual
installation of the public open listener before product actions; it does not
mock keyboard or storage delivery. Initial hydration readiness is separate.

Eighteen focused source/kernel checks pass (seven new, eleven shared), with
five source/UI mutation controls. Next typegen and frontend TypeScript pass.
Required root nine-capture/six-tooling and app698-object/npm/unchanged-SDK
checks pass. The actual caller/persistence fingerprints cover their bounded
operations and remain separate from unrelated shared dialog rendering.

## Fresh-main integration

After live overlap review, main `60bdd8a7a522921058d18563bb9335d2a06aec75`
still lacked this history workflow. It already includes separate Escape,
shortcut, delayed-clear and local-user-search changes. The history-only
integration preserves them and has its own fresh before/after proof in
[`current-main-60bdd8a7/VALIDATION.json`](current-main-60bdd8a7/VALIDATION.json).
The untouched base again fails the first new case after two actual form
submissions and reload (one fail, four not run; max-failures1). The candidate
passes all five new history cases plus nine existing search cases: fourteen
in two finite commands, workers1/retries0. Those include populated Escape at
both viewports, all three mounted-shortcut cases, delayed Clear, real local
profile navigation, URL/history/empty behavior and keyboard traversal.

The original add/clear/href AST bindings and persistence fingerprints remain
identical. All eighteen focused source/kernel checks, Next typegen/frontend
TypeScript, required nine-capture/six-tooling checks, app698-object/npm/SDK
integrity and progress freshness pass again on these integrated source bytes.
Four new inspected screenshots bind this cohort separately. The old31cea
packet, source commit `3adb2e3f49`, and its image/JSON/validation bytes remain
preserved; its seven browser results are not transferred to the new image.
No full production build or aggregate browser suite is claimed.

For the fresh finite browser run, use the command above plus
`tests/search-dialog.spec.ts tests/search-shortcuts.spec.ts tests/search-local-users.spec.ts`,
adding `delayed search clear|Escape dismisses populated|bare slash|searches the local user model`
to the grep, then run `tests/search-shortcuts.spec.ts --grep 'Ctrl-K toggles' --max-failures=1`.
The checked-in current logs retain the exact selected cases. A preliminary
source check before UI integration correctly rejected the missing history
import; a typegen invocation from outside the package hit a package-manager
version guard. The final checks used the app/frontend directories and passed,
without changing dependencies or relaxing the source checks.

Run from `app`:

```sh
node scripts/verify-recent-searches.mjs --check
node --test tests/recent_searches.test.mjs tests/original_source.test.mjs
```

Run from `app/packages/frontend`:

```sh
corepack pnpm exec playwright test tests/recent-searches.spec.ts tests/shell.spec.ts --grep 'real submissions|strict duplicate|malformed local|failed history|real same-origin|search encodes queries|keyboard traversal reaches' --max-failures=1
corepack pnpm exec next typegen
corepack pnpm exec tsc --noEmit
```

The recorded run used the normal config with webServer disabled against its
already running owned dev server on 127.0.0.1:3010, workers1/retries0. No test
timeout/sleep was increased. That server is stopped. Four inspected PNGs show
the same actual-input/reload actions at desktop1280×800 and mobile375×812.
The baseline key is absent and the candidate persists the two submitted
strings with their encoded links. `VALIDATION.json` binds the full historical
UI/test and observation bytes. Subsequent main merges are not silently
relabelled as part of this frozen cohort, and no separate Escape/shortcut
overlay inherits these runtime passes.

These are synthetic local input controls and maintained-app references, not
upstream response fixtures, production records or original visual parity.
No backend/API/auth, captured artifact, SDK/dependency, shared framework,
feature-progress milestone or binary changes are included. Full Next/build,
aggregate browser suites, other engines/input methods, complete SearchDialog
and production compatibility remain separate qualifications.
