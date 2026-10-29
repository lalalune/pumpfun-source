# Prize displays on the web competition detail page

The accepted original prize components were not mounted in the maintained web
detail view. An empty standings response with supplied prize tiers therefore
showed only the generic empty-results message; ranked rows omitted their supplied
rank-selected prize. This integration connects the existing components to the
already-validated web response.

The condition is the captured coordinator's: use prize tiers when the **raw**
standings are empty and supplied prizes exist. It does not use the filtered
visible row count. A search with no matches on an existing board retains the
existing empty-filter state. Ranked rows use the complete accepted `706615.J`
first-inclusive-range lookup and the original raw-text badge. There is no rank,
prize allocation, entitlement, registration or backend-policy calculation.

## Sources and local providers

Accepted PR937's full D/T/badge component bytes are unchanged and still pass its
strict source verifier. The new verifier authenticates the original selector and
planner witnesses, verifies actual page/row prop bindings and the raw-empty
condition, and checks that existing native formatting functions are unchanged.
Captured factories remain inert. Reused original code receives no new recovery
count or claim of private source paths.

The maintained page is English. Its bridge reuses the existing captured English
prize-only labels from accepted PR864 and the existing precise BigInt amount
formatter. Export aliases share those existing implementations; their bodies
are unchanged. The original components receive these explicit local providers.
No global original NumberFormat variant is selected. This deliberately retains
the web precision fix rather than reintroducing Number conversion for large
decimal strings. Original formatting/provider parity is not claimed.

All displayed prizes and ranks come from the existing response. API routes,
projection/types, ranking, PnL, auth, SDK, captures, dependency/lock files, global
styles, feature ledger and completion counts are unchanged. No native/mobile
app, app promotion, app-store/deep-link or QR flow is implemented.

## Verification

    node scripts/verify-competition-prize-page.mjs --check
    node --test tests/competition-prize-page.test.mjs \
      tests/competition-prize-precision.test.mjs tests/competition-rules.test.mjs \
      tests/original_source.test.mjs
    pnpm -r typecheck
    python3 scripts/verify-evidence.py

Source/SSR checks cover the actual component, exact first-match boundaries,
rank-zero/no-match absence, immutable supplied order/text, escaping and large
decimal precision. Deliberate selector and filtered-empty changes fail the
source gate. A real loopback JSON read passes the retained public response
schema, actual bounded decoder, projection and client admission before original
tier rendering; malformed numeric prize text is rejected. This is finite
frontend plumbing proof, not a private backend compatibility claim.

The five targeted Next/browser cases use the actual `/leaderboard` page at
390/1280 widths: empty supplied tiers, ranked badges, filtering without a false
tier fallback, and empty standings without prizes. Browser transport uses
explicit synthetic local adapter envelopes and blocks external/mutating
requests; it does not exercise backend transport. Exact baseline source files
are retained in `reference/` for the same before/after page assertion.

The final browser method reproduced both missing-region failures on the exact
base files, then passed all five fixed cases (14.1s). Both widths preserve the
large decimal and avoid horizontal overflow; submitted local filters preserve
the adapter-read count and never turn a populated board into a tier fallback.
The initial fixed run had two passes and three test-harness failures: StrictMode
mounted one first-read twice, and the test filled a submit-only filter without
submitting. Those raw results are retained. The final method permits initial
StrictMode duplicates, submits the actual Filter button, and measures reads
across those local actions. Product code did not change for these corrections.

The executed Next recipe is finite Webpack dev with shared read-only dependencies
and no backend server. This is actual mounted-page/browser proof with synthetic
read-only adapter envelopes, not a full production build, backend transport,
original provider parity or universal compatibility claim. Source/SSR23tests,
all three workspace typechecks and698capture/npm/SDK integrity checks also pass.
See `qualification/` for exact source/tree bindings, commands, raw logs and PNGs.
The complete app suite and production Next build were not rerun in this lane.
