# Archived Live details and composing Escape

Base: `b08fd908203a76d84c8dd68b60310582aa2c4fba`. Its complete app tree is
identical to main `630a074126a13d4133514d599129c6ac9a3179bc` at the publication
check (`e3d6d8cd07df4f561a4fd058dad29d22de451bfc`).

The single changed production condition ignores `KeyboardEvent.isComposing`
when deciding whether Escape dismisses the nonmodal archived metadata panel.
Existing normal Escape, modal/default-prevented ownership, selection readiness,
tab navigation and data/playback boundaries are preserved. Ordinary navigation
continues to clear a fragment; the composing event must preserve the exact URL.

The native HTML dialog is a **platform control**, not an original Pump UI or
player. Both control and app receive trusted Chromium CDP composing keydown.
Before: native control leaves the default available and stays open; Live prevents
the default, leaves composition active on keyup, removes `stream` from the URL
and closes the metadata. After: the app leaves the default available, composition
ends, the exact selected URL/detail/focus remain, and the next ordinary Escape
still dismisses as before. The tests do not construct synthetic KeyboardEvents.

Native-input methodology follows the comparison used in related Settings PR
#1304. No Settings implementation is copied or modified. Open #1449's readiness
and #1328's tab navigation remain separate: authenticated peer file hashes and
source-only apply checks, separately and together, are retained. They are not
runtime integration/equivalence evidence.

## Executed checks

- Complete-input exact base: the IME target fails; the unchanged adjacent profile
  status control passes. Final baseline and candidate use the same test method.
- Candidate: **18/18 browser cases pass**, two new trusted comparisons at 390/1280px
  plus all 16 maintained Live cases. Queries/focus, normal dismissal, modal
  ownership, pagination, timing-sensitive controls, local requests and archived
  boundaries remain checked.
- **15 Live snapshot/filter tests**, frontend TypeScript, 698-object/npm/31-SDK
  integrity, progress freshness and nine progress tests pass. Exact public-head
  required root checks are recorded in the PR after publication.

The run used 3019. The maintained suite's one hardcoded safety-origin literal
was changed only in an executed temporary copy; GET/HEAD and exact-origin
assertions remain strict. Both the actual copy and diff are retained; original
`live.spec.ts` is unchanged. The existing already-closed local browser preference
fixture was remapped to 3019, without inferring original consent/authentication.

From `packages/frontend`, with the retained config beside `playwright.config.ts`
and the retained temporary control copy beside `tests/live.spec.ts`:

```
LIVE_IME_PHASE=final corepack pnpm exec playwright test \
  --config playwright.live-ime.tmp.ts \
  tests/live-ime.spec.ts tests/live.serial-port.tmp.spec.ts
```

The first broader attempt hit missing sparse profile fixture input, not a new
profile regression: the actual UI was `profile-data-error`, returning 200.
The exact Git posts/following seeds were restored; their hashes and unchanged
users seed are retained. Profile product code and assertions were not changed.
That initial 8-pass/1-fail/9-unrun log is preserved privately and is not relabelled
as a final pass. A local Next not-found doc check also distinguishes streamed
not-found HTTP200 behavior; it was not the observed missing-input branch.

`checks.json` binds actual source/test hashes, raw extracted native/app JSON,
commands, logs and screenshots. Log gzip files are lossless, including terminal
whitespace. Full reports/traces and initial diagnostics remain private. Screenshots
are local state evidence, not original references or a pixel-parity claim.

No live stream, player, production API, wallet or chain operation is started.
No production build, broad suite, backend/native compatibility, security clearance
or completion credit is claimed. Captures, SDK, backend and dependency bytes are
unchanged.
