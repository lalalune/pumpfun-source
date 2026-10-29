# Readable Rules schedule columns

At 390px, the native Rules schedule splits the single words `Registration` and
`Competition` across two lines. Its date values keep an intrinsic flex basis
and consume width needed by the labels. The captured complete `590407.tr`
schedule helper instead gives its value span `min-w-0 flex-1 text-right`.
The stylesheet linked from the captured leaderboard HTML defines `.flex-1`
as `flex:1`.

This fix adds a schedule-only class to the existing `dl` and gives its `dd`
values that remaining-space allocation. Prize rows, labels, dates/UTC policy,
number formatting, models, API/backend and dialog dismissal are unchanged.
`source-evidence.json` binds the actual helper/callers, original capture, CSS
declaration range/hash and HTML stylesheet context. It is source evidence,
not a newly recovered component, provider or visual-parity claim.

The unit branches directly from main `094a06f1`. PR #1751 is a **tooling-only
reference**, not a feature ancestor: four exact public loopback harness files
are hash-verified and prepared temporarily. Their source is not duplicated in
this PR. Its source/HTTP qualification is credited, without transferring its
test or production result to changed runtime code.

From `app`, with the pinned existing dependencies:

```sh
# Offline preparation from the four pinned public Git blobs; no install/fetch.
python3 reconstruction/competition-rules-schedule/prepare-fixtures.py
# If those objects are unavailable, use an existing #1751 app checkout instead:
# python3 reconstruction/competition-rules-schedule/prepare-fixtures.py --source-dir /path/to/reference/app
# Reserve one Next slot. The unchanged referenced tools own/close the servers.
PUMP_RULES_PORT=3027 PUMP_SCHEDULE_PHASE=fixed node packages/frontend/node_modules/@playwright/test/cli.js test --config reconstruction/competition-rules-schedule/probe.config.mts
python3 reconstruction/competition-rules-schedule/prepare-fixtures.py --clean
```

Preparation refuses different existing files and verifies size/SHA-256/Git blob.
Cleanup removes only matching untracked copies. No reference source files
belong in the commit. The finite probe is evidence tooling, not an additional
maintained test suite for this one CSS property.

The same-data actual Next GET → existing Fastify handler/default synthetic
competition seed measures real DOM text ranges, widths and overflow at 390px
and 1280px. It does not fulfill JSON or alter fonts/clocks/DOM layout properties.
The referenced child constructs a public synthetic key, reads no parent key and
keeps the native API gate. No real account, signing or network mutation is used.
Exact phase heads, raw observations, comparison and limits are retained in the
qualification packet. Full app/browser, original production API/provider and
pixel parity remain unqualified; no milestone or financial calculation claim.
