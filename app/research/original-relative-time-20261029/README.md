# Original feed relative timestamps and clock read

This reconstructs the captured relative-time UI and its used clock chain in the
existing Home/native-callout feed. The captured client requests
`GET /api/server-time`, accepts a successful JSON object with finite numeric
`nowMs`, and derives a clock offset from the request/response midpoint. The local
Next GET handler supplies its actual wall-clock time to that observed contract.
The original server's internal implementation and headers are unknown.

## Source closure

[contract.json](../../reconstruction/relative-time/contract.json) binds the
immutable manifest/inventory and exact source URLs, hashes, UTF-16/UTF-8 ranges,
registered exports, and inert fragments. The complete used path is:

- Actual registered `204478.f` callout card → its direct `529841.f` timestamp use.
  The shared factory contains other registered IDs; they are not substituted for
  this consumer.
- `529841.f` → `633311.l` timestamp normalization, `632817.H` shared display clock,
  `170450.f` mounted state and used `890088.f/K/V` formatting branches.
- `632817` → `668487` corrected time and sample request, with one shared aligned
  timer and visibility/subscription handling.
- Both retained physical `890088` variants are bound. The English unit/suffix
  values come from a literal `locale=en` resources row in a real Next Flight
  push inside authenticated HTML. Babel only parses inert script syntax; JSON
  rows are decoded as data. Captured JavaScript is never run.

The already maintained notifications-inbox source binds `668487.t` as injected
current time and expressly excludes synchronization. That attribution is a
prerequisite with zero new credit here; notification files and behavior are
unchanged. No complete original route/locale or server-internals equivalence is
claimed.

## Preserved behavior

The clock shares one in-flight request, uses `cache:no-store`,
`credentials:omit`, and a five-second abort signal. Differences strictly below
five seconds are ignored; larger differences round the midpoint correction.
Success is eligible again after fifteen minutes, failures after one minute.
These are eligibility deadlines: sampling is triggered by the first subscriber
or visibility restoration, not by every display tick.

The display timer aligns to corrected second boundaries, pauses while hidden,
and uses the captured zero server snapshot/mounted selection. Timestamp numbers
below `1e10` use seconds; other finite numbers use milliseconds. Date/string and
invalid/null behavior is preserved, including no new Date-range guard. Relative
labels floor units, clamp future/subsecond ages to one second, and use months of
30 days and years of 360 days. The UI keeps ISO `dateTime` and exposes the captured optional
absolute title. This application's implemented labels are English only. The
original custom-class/Tailwind merge option is not exposed, and no pixel
identity is claimed.

The source's callback rearms after notification even when its last subscriber
unsubscribes synchronously inside that notification. A focused test retains this
bounded edge explicitly; cleanup claims apply to ordinary unsubscribe outside
notification. No blanket leak-freedom or security claim is made.

## Verification

From `app/`, with existing pinned dependencies:

```sh
node scripts/original-relative-time.mjs --check
node --test tests/original_relative_time.test.mjs tests/original_source.test.mjs
corepack pnpm test:feed
corepack pnpm --filter @pump-reconstruction/frontend typecheck
python3 scripts/verify-evidence.py
python3 -m unittest discover -s tests -p test_progress.py
```

From `app/packages/frontend/`, in the serialized browser slot with ports3001/3016
free:

```sh
corepack pnpm exec playwright test --config playwright.relative-time.config.ts
```

The dedicated `.flow.ts` file joins only its explicit configuration. Its input
server is an authored GET-only loopback fixture, not an original/backend product
implementation. The actual Next UI and `/api/server-time` route execute; no
production calls or captured bundle execution are used. The final same-harness comparison is recorded in
[VALIDATION.json](VALIDATION.json): the base intentionally passes its expected
absolute-text/missing-route check, and the changed workflow passes its actual
clock-read/display checks. This is not a baseline failing assertion. No full
production build or general browser-suite pass is claimed.

No validator, original capture, seed, SDK source, auth/session mechanism, social
mutation, financial operation, global ledger or compatibility qualification is
changed.

## Actual bounded browser result

Browser-tested code is `a5c8b8174d6797c1e1eed4ab79052ac36a5dbbe3`;
product source is unchanged from `4eeae0466003bdb363f569c1c451764fb226c065`.
Both runs use the same canonical timestamp in the validated native DTO input.
The base renders its absolute timestamp and returns404 for the absent local
clock route. The changed run receives a genuine Next GET200, verifies its finite
wall-clock result/no-store header, applies correction, ticks, and shares one
browser request across the native card and subsequent three-post SPA view.
An extra test-runner GET and unsupported local POST405 check the read handler.
No social/financial mutation occurs.

A finite hydration observation matters: with client Date two minutes fast and
one time request held, the actual DOM retained its server-rendered `31s ago`
label. The captured `suppressHydrationWarning` path can leave that text in place
when hydration/mounting selects the same virtual text bucket. One documented
60-second Date advance caused a genuine display transition to `3m ago`. The test
restored the initial Date before releasing the real response, preserving the
sampler's midpoint. It then observed correction and a later display tick. It
does not claim that initial client drift was immediately visible in the DOM.
Earlier observation-point failures and traces remain preserved privately;
product hooks/model were never replaced to satisfy the test.

The successful test checks the actual response value against test-host time and
bounds the corrected display using that response plus the record timestamp.
The exact response JSON value and corrected pre-tick text were not separately
serialized in the retained line-reporter log. The before/after transition data,
actual endpoint statuses and complete passed assertion source are retained.

- [Expected-absence baseline screenshot](proof/baseline-1280.png)
- [Changed desktop screenshot](proof/candidate-1280.png)
- [Changed mobile full-page screenshot](proof/candidate-375.png)
- [Baseline browser/HTTP/Next log](proof/browser-baseline.log)
- [Changed browser/HTTP/Next log](proof/browser-candidate.log)

The mobile assertion covers horizontal overflow and CSS visibility. Its raw
full-page image has a pre-existing fixed navigation overlay over the card footer
at that position. Footer visibility at every scroll position, hit-test behavior
and pixel parity are not qualified by that image.

[MANIFEST.json](MANIFEST.json) hashes this retained proof. From this directory:

```sh
python3 - <<'PY'
from pathlib import Path
import hashlib, json
for row in json.loads(Path('MANIFEST.json').read_text())['files']:
    data = Path(row['path']).read_bytes()
    assert len(data) == row['bytes']
    assert hashlib.sha256(data).hexdigest() == row['sha256'], row['path']
print('Retained proof hashes pass')
PY
```
