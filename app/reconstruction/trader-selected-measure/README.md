# Selected trader PnL measure on the native web board

Changing the maintained trader board to Realized or Unrealized already requested
and received rows ranked by that measure, but `TraderRows` always displayed
`pnlUsd`. A supplied row with combined 100, realized -20 and unrealized 120 therefore
still showed a green `$100.00` after selecting Realized. The row now receives the
same selected sort used by the request and displays the corresponding supplied
field. Realized displays `-$20.00`; Unrealized displays `$120.00`.

This restores the complete raw-score decision from the accepted #829 source
recovery. Both physical `996005` consumer variants actually pass the chosen sort
through the query and into the row, where `416287.n(entry,sort)` supplies the
rendered amount/tone input. The gate binds the whole original request/query/
selector recovery, both complete row-consumer contexts, actual query options,
selected-value formatter/tone calls and actual row prop ownership. Captured
factories remain inert. These discoveries are reused without a new source
recovery count or a dependency on unaccepted competition port components.

The existing native Intl currency policy and native sign/zero tone policy are
retained; they now consume the selected value. Original `540805` formatting and
neutral-band parity are not claimed. The existing combined percentage caption
is retained only for Combined; partial measures use the same native Realized/
Unrealized labels as the control. No partial-return percentage is calculated or
inferred. Realized/unrealized detail facts, identity, supplied rank/order, API
routes/types, upstream decoder, key handling and backend rules are unchanged.

## Actual local read flow

The existing maintained native `LeaderboardStore` and Fastify handler serve the
owned loopback fixture. Its hand-authored synthetic seed supplies all measures;
this unit implements no ranking, PnL arithmetic, pricing or backend business
logic. An ordinary missing-key HTTP read receives 401. Proper fixture requests
retain the existing key gate and produce actual 200 responses, sorted by the
existing handler. The exported maintained Next adapter is also exercised through
an HTTP bridge, its bounded decoder and actual client admission before real
React row rendering. Unsupported adapter filters fail before an upstream call.
Stopping the owned backend produces a genuine adapter 502; restarting restores
200 without a substituted row set.

The explicit browser harness starts one owned Next Webpack-dev process and the
same local native backend. Its server-only test preload redirects exactly the
existing developer PnL read to that owned loopback service, preserving path,
query, method, headers, signal and no-store options. The browser uses the actual
Next API route and does not receive fulfilled JSON mocks. It blocks foreign
origins/mutations and checks that the synthetic test key stays off browser
requests/HTML. The key is generated explicitly in the child environment, never
read from parent credentials. No user cookie/profile, wallet, signing or live
service is used. Both services are closed by the finite fixture controller.

This is functional local read-model/UI proof with explicit synthetic provenance,
not original API/backend/provider compatibility or a security acceptance claim.
The captured website's cookie/client/query/wallet capabilities are not replaced
by this operator-key read adapter. Global API/feature compatibility counts and
prior frozen evidence remain unchanged.

## Commands and scope of evidence

From `app` with existing pinned dependencies:

    node scripts/verify-trader-selected-measure.mjs --check
    node --test tests/trader-selected-measure.test.mjs tests/original_source.test.mjs
    pnpm -r typecheck
    python3 scripts/verify-evidence.py

The focused suite has four new source/negative/real-HTTP/actual-React cases and
11 reused source-reader cases. Its exact base function is retained in
`reference/`; the source gate records its original Git file/range/hash. Before
rendering uses that complete base row and its unchanged real helpers. Candidate
SSR bundles the actual native module, exposing only its existing private row to
the test without replacing its product body.

The dedicated opt-in browser suite is outside the default frontend testDir so a
normal broad browser run does not launch another dev server. Reserve one local
Next slot before this finite command; its fixture owns and closes that server:

    PUMP_MEASURE_PORT=3027 PUMP_MEASURE_PHASE=fixed \
      node packages/frontend/node_modules/@playwright/test/cli.js test \
      --config tests/browser/trader-selected-measure.playwright.config.ts

Use `PUMP_MEASURE_OUTPUT_DIR` for a separate owned output directory, and
`PUMP_MEASURE_CHROMIUM` to select the already-installed matching browser on
another machine. No install or lockfile change is required. The browser cases
cover both widths, all three valid measures, actual backend responses before UI
assertions, genuine upstream stop/Retry and absence of stale ranking rows.
Actual before/fixed browser results and independent production/root checks are
separate pending gates; no full app/browser suite is claimed here.
