# Foreground refresh on the native competition web page

An already-open native competition page previously fetched only on query change
or Retry. A changed supplied title or ranked-row measure therefore never appeared
until the user navigated or retried. The accepted original read workflow (#868)
passes a 60-second list interval and a 15-second detail interval to its query
provider. Both physical foreground modules require a visible document **and**
focus. The actual captured Cup consumer calls these list/detail hooks.

The native page now uses those intervals and the shared original foreground
predicate for recurring reads through its existing `/api/leaderboard` adapter.
Initial reads remain unconditional, including when the page lacks focus. Hidden
or blurred pages cancel future scheduled reads; an already-started read can
settle. Returning to foreground starts a new full interval. Each recurring read
waits for settlement before another interval starts, avoiding overlapping polls
in that controller. Equivalent focus/visibility snapshots do not reset the timer.
Changing the native query or unmounting cancels its timer, subscriptions and owned
browser request. Aborted or superseded responses cannot update the page.

The current validated page stays mounted during a background read. A validated
response updates it; an admitted error or invalid response clears the ranking
view using the existing error/Retry boundary. Trader and creator reads retain
their single-attempt behavior. Local filter, pagination and rule-dialog actions
do not manufacture an additional request or a new refresh policy. API routes,
types/admission, credentials, backend stores, phase/ranking/financial rules and
the original captures/SDK remain unchanged.

## Source boundaries

`scripts/verify-competition-refresh.mjs` reuses the complete accepted #868
producer, strictly attributes `359516.f` and `961415.f` to their real export slots
(excluding the unrelated co-registered portfolio export), and binds their actual
`85324.q` calls and complete foreground snapshots. The two physical snapshots
have the same AST, so the native predicate needs no arbitrary global variant
winner. It binds the actual mounted effect, returned cleanup, existing GET,
abort signal and response admission. Negative tests reject a wrong cadence,
visible-OR-focused predicate, discarded cleanup and detached request signal.
No captured bundle is executed and no new recovered-factory count is claimed.

The original list/detail `staleTime` descriptors (15 seconds / 5 seconds), query
keys/viewer scope, detail's **literal-null-only** disabled projection and query
provider focus/cache/retry defaults remain source facts in the reused evidence.
This native scheduling port does not implement that provider or infer its cache
semantics. Native URL parameter admission remains with the existing adapter;
an empty native competition value continues to mean a list read. The local
completion-relative scheduler is explicitly different from a claim about the
original provider's timer runtime. The existing Next route also owns its own
upstream deadline; canceling the browser request does not establish a new claim
about cancellation of an already-issued upstream request.

## Repeatable bounded checks

From `app` with existing pinned dependencies:

```sh
node scripts/verify-competition-refresh.mjs --check
node --test tests/competition-refresh.test.mjs tests/original_source.test.mjs
pnpm -r typecheck
python3 scripts/verify-evidence.py
```

The focused suite exercises the real existing Fastify handler and actual exported
Next GET through a loopback HTTP bridge, including changed supplied seed facts,
ordinary missing-key 401, genuine upstream stop 502 and restart. The seed is
explicit synthetic data and reseeding is confined to a private test controller,
not a public mutation API. The test-only key is generated explicitly in the
child environment; no parent key, user session/profile, wallet or live service is
read. The existing key gate remains active.

The dedicated browser suite uses the actual Next page/API and the same actual
native handler, with narrowly scoped server-only upstream redirection. Browser
requests are continued or aborted, never fulfilled with JSON. It uses real
elapsed time for both intervals, actual tab focus/foreground, upstream failure/
Retry and unmount. Reserve one coordinated Next slot before running:

```sh
PUMP_REFRESH_PORT=3027 PUMP_REFRESH_PHASE=fixed \
  node packages/frontend/node_modules/@playwright/test/cli.js test \
  --config tests/browser/competition-refresh.playwright.config.mts
```

The exact same-method baseline failed the two cadence cases: the detail stayed
at `$100.00` for 22 seconds despite a real changed backend response of `$200.00`,
and the list kept snapshot 1 for 68 seconds despite a real snapshot-2 response.
The original fixed batch passed both cadence cases, with actual Next-response
gaps of **15,035ms / 60,019ms**, then failed the focus fixture's precondition.
Pinned Playwright forces focus emulation for each new main frame. After disabling
that driver override in the correct frame order, the focused lifecycle case
passed separately: the visible source document's native focus was false, no
read occurred for 17,043 real milliseconds, foreground return refreshed data,
actual upstream failure yielded Next 502/no stale rows, Retry restored data,
and unmount stopped recurring reads. No DOM property override or fake event was
used. The original batch and intermediate fixture failure are retained; this is
**two cadence passes plus one focused lifecycle pass**, not one clean three-case
run. The complete shared setup and first two callbacks are byte-identical across
the harness-only corrections, and the product source is unchanged. The finite
packet records their distinct tested heads and preserves the earlier failures.

Independent production/common checks remain pending. Synthetic local behavior does not qualify original production APIs,
authentication, query-cache/runtime parity, financial derivation, visual parity
or feature milestones. Test instrumentation reuses the finite child/Next
controller pattern from #1600; that scaffolding is attributed, not claimed as a
second source recovery. Existing accepted or pending source packets remain
frozen and this unit has no Groups or native-app promotion scope.
