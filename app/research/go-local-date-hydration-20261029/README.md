# Hydrate GO dates without changing browser-local formatting

GO's mounted archive rendered `new Date(value).toLocaleDateString("en-US")`
directly during both server rendering and hydration. For the same retained
created timestamp, `2026-10-28T06:53:34.915Z`, the UTC server emits 10/28/2026
while a Los Angeles browser renders 10/27/2026. React reports that exact
`GoExplorer` card `<time>` mismatch and regenerates the boundary on the client.
The existing expiry rendering has the same source pattern.

The bounded correction uses a GO-only `GoLocalDate` component at both sites,
following the installed Next guide for this exact problem. It reuses the
existing unchanged `InlineScript`: a stable React ID identifies the time
element, a parser-time script formats its text in the browser, and the client
script is inert. JSON serialization plus `<` escaping protects embedded string
literals. Warning suppression is confined to the expected local-date text;
the measured native browser label is also asserted, so this does not merely
hide a stale server label.

The timestamp and `en-US` format remain unchanged. Browser-local timezone
behavior is preserved; this does not introduce a UTC display policy. There
is no new clock, sampler, global listener, data request, shared-helper change
or date-derived state/effect.

## Exact before/after boundary

| Measurement | Actual result |
| --- | --- |
| First harness `978de6705755a81247304de2992ef97688ae3c96` | Date-specific hydration error captured, but first reached assertion failed on the aborted Next development-overlay diagnostic POST. The later hydration assertion was not reached. |
| Corrected causal harness `61ae6c8d59ea9597ce047acf0d8fed090828cb51` | **1 failed**, now at the intended hydration assertion, line 47. Only the two assertion lines were swapped. Guard and product source remain unchanged. |
| Candidate `d6d7c3baef91d8160ac8056f83d697c2b4fe69ef` | **14 passed in 34.6s**: byte-identical causal flow, expiry navigation/reload control, matching UTC control and eleven unchanged GO cases. |

Both baseline attempts retain the actual SSR HTML date 10/28 and the native
LA browser date 10/27. The exact React diagnostic names the card `<time>` and
shows those two labels. The failed attempts abort and record
`POST /__nextjs_original-stack-frames`, which the development overlay tries
after the React error; it is not allowed through and is not a domain mutation.
No POST exceptions were introduced. First and corrected logs, JSON and full
private negative traces remain distinct; no failure is relabelled.

The same candidate flow records the same server/browser labels with
**`errors:[]` and `forbidden:[]`**. It reads the original navigation response
as inert HTML to record SSR text and observes the actual mounted date after
hydration. Neither responses nor browser date functions are replaced. The
additional controls cover actual expiry text on direct load, soft navigation
and reload, plus unchanged UTC output. The 3 new cases allow only local
GET/HEAD and do not fulfill responses. Retained cases include deliberate
error/malformed-response fixtures; those are not live API qualification.

The candidate's full raw log also contains the separate shared SearchDialog
hydration warning during a retained query/history case. This packet does not
change that shared component or claim whole-app console cleanliness. The
date-specific focused cases pass without hydration errors. Settled screenshots
are retained; there is no paint-by-paint timing measurement. The synchronous
parser-script strategy is source-derived from the installed Next guidance,
not an independently measured first-paint claim.

## Provenance and scope

Base main: `094a06f18df738d41e77070c1a009e135671ac1a`. Both baseline attempts use
its unchanged product source. `VALIDATION.json` binds all measured code,
source/harness hashes, guidance hash, actual commands and private trace hashes.
The existing capture/loader/validator, API, query/cursor/filter/sort/task logic,
SDK, dependencies, feature ledger and prior packets are unchanged. The source
is a maintained-host defect fix, not recovered original GO interaction code.

No captured original JavaScript is evaluated. The existing authenticated GO
HTML/RSC archive is still parsed as data. There is no live service, auth,
wallet, submission, funding, payout, original visual parity, production-browser,
compatibility or milestone claim.

Related work remains separate: #1369 changes shared SearchDialog hydration;
#1612 fixes GO pending search-draft ownership; #1344 validates cursors; #1469
positions task deep links. This PR changes the two date-rendering sites only
and does not copy those implementations.

## Reproduce

With the pinned dependencies available and port 3010 free:

```sh
cd app/packages/frontend
corepack pnpm exec playwright test --config playwright.go-dates.config.ts
```

Expected: 14 passed. The server uses `TZ=UTC`; the default browser timezone is
`America/Los_Angeles`, with an explicit UTC preservation control. To reproduce
the causal baseline, use a separate checkout of the base, copy this PR's
`tests/go-date-hydration.flow.ts`, and copy this packet's
`baseline-playwright-config.txt` into
`app/packages/frontend/playwright.go-dates.config.ts`. Run the same command.
Expected: one failure at the hydration assertion after recording the actual
date-specific React error. The unmodified safety guard may also record an
aborted overlay diagnostic POST; that later assertion is not reached.

The fixed-flow source is byte-identical to the corrected baseline. Candidate
selection expands only; the Next command, UTC server, default LA browser and
guard remain unchanged. No source correction or timezone-policy variant was
tested between the recorded fixed source and the successful run.

Headless checks passed: 8 GO model tests, frontend typecheck, 698-object/npm/
unchanged-SDK verification, progress consistency plus 9 tests, 9 repository
captures and 10 tooling tests. Repeat with the repository's usual commands:

```sh
cd app
corepack pnpm test:go
corepack pnpm --filter @pump-reconstruction/frontend typecheck
python3 scripts/verify-evidence.py
corepack pnpm check:progress
cd ..
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

`MANIFEST.json` binds raw/compressed log hashes and all packet bytes. Later
packet-only commits preserve the measured source and harness; publication
records the exact local/public tree mapping separately.

## Independent normal build receipt

The exact public source `7f1b5ff94b44b2209c00ef1c9d42ff64682d36f4` also passed
an independent normal SDK/backend/Next production build, all workspace
typechecks, 698-object/npm/unchanged-SDK evidence verification and progress
checks. `ROOT-PRODUCTION.json`, the exact checks JSON and four compressed raw
logs retain that result. Seven output manifests remain independently retained
with their hashes recorded here.

This later change is receipt-only: README/manifest plus those six receipt
files. All source, harness, captures, dependencies and SDK bytes remain the
tested public source. This proves a normal production build, not deployment,
production traffic, an additional production-browser run or extra timezone
parity. The original 14-case development browser evidence and limits remain
unchanged.
