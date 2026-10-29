# Original standalone quote previews

The maintained local examples page omitted all recorded quotes. This unit
reconstructs the captured standalone `386028.f` preview and mounts it beside
the existing unchanged `FeedItem` in that page. Home opts into a new local join
that admits the three hash-bound quote records; its three root records remain
unchanged. Profile/default projections remain root-only. Reposts remain excluded.

## Source and dependency boundary

[contract.json](../../reconstruction/quote-preview/contract.json) records exact
factory/source hashes, original URLs, UTF-16/UTF-8 ranges, and verbatim inert
fragments. Its producer authenticates the retained manifest and full inventory
before parsing the original registration AST. Captured JavaScript is never
imported or evaluated.

The actual registered `386028.f` export is the preview; the same factory also
registers a different `390767.f` route helper. All three physical preview
variants are retained, without selecting a running variant. Visible text calls
the actual `174251.f` export, which resolves to the memoized `N` component. It is
not an assumed `N` export. **PR #1374, public head
`7f1f6627b8e3aae1d7e4a9c99c2652202549a0cd`, is an explicit prerequisite with
zero new recovery credit.** This branch uses that exact public ancestry and
leaves its `FeedItem`, `NativeCalloutFeed`, model, source contract and renderer
unchanged. Shared authenticated-source tooling is also prior work.

The source computes the nullish author-name/address fallback with the used
`365089.d(address, 4, 4)` helper, including its nine-character threshold. Empty
author names suppress the fallback; whitespace names remain untrimmed. Deleted
previews show only the known translation key, while visible nonempty text uses
the prerequisite mention renderer. The original English translation for
`profile.reposts.deleted_post` was not found in retained inputs. The host
explicitly injects the **local** copy “Quoted local record unavailable.”

Actual owning source bindings are retained: `349919.f` passes the result of
`287129.g(row)` into the preview, and three `910976.f` physical variants pass a
quote envelope and density. These establish real original call bindings, not a
unique active runtime or complete reconstructed original route. The captured
`287129.g` operates on parent-reply/callout envelopes. It is **not** the legacy
seed join introduced here.

## New local host adaptation

The existing legacy seed has `quotedPostId` references rather than those modern
envelopes. The authored opt-in `includeQuotes` projection resolves references
after validation, handles forward references without recursion, and withholds
hidden/deleted/missing target content. Unresolved target authors do not become
fabricated preview names or wallets. Media URLs stay withheld; no fetch is
introduced. Recorded counters are displayed unchanged. Root validation/order,
default root-only reads, and input immutability are retained.

This local policy and coordination are new application code, not recovered
original server behavior. The mounted preview exposes only standalone
comfortable density. Dense/terminal rendering, original CSS/pixel identity,
translation parity, repost actions, social mutations, auth, API compatibility,
backend recovery, feature-ledger completion and milestone credit are excluded.
The native callout DTO and backend `quote:null` boundaries stay unchanged.

## Reproduce

From `app/`, using the existing pinned dependencies:

```sh
node scripts/original-quote-preview.mjs --check
node --experimental-strip-types --test tests/quote_preview.test.ts tests/original_mention_text.test.mjs tests/original_source.test.mjs
corepack pnpm test:feed
corepack pnpm test:profile
corepack pnpm --filter @pump-reconstruction/frontend typecheck
python3 scripts/verify-evidence.py
python3 scripts/progress.py --check
```

From `app/packages/frontend/`, with port3016 free:

```sh
corepack pnpm exec playwright test --config playwright.quote-preview.config.ts
```

The dedicated `.flow.ts` story uses the actual Next page and unchanged
hash-bound at-rest seed loader; no test endpoint or seeded HTTP replacement is
added. It blocks nonlocal browser requests and browser mutations. The same
story can assert the base's expected absence with
`QUOTE_PREVIEW_EXPECT_BASELINE=1`. A passing expected-absence baseline is not a
baseline assertion failure. The candidate checks three mounted previews,
recorded ordering/content, unchanged roots/counts, excluded records, profile
keyboard navigation, and desktop/mobile overflow. Unavailable states are
covered by source/model/join tests, not a claimed mounted browser observation.

## Retained result

[VALIDATION.json](VALIDATION.json) binds the actual browser-tested code revision
`69e05783f8b260c607486196685dbbf5316f4b63`, the four restored host files, harness,
unchanged seed inputs and prerequisite files. Both runs use the actual same
immutable seed. The retained controller restores the candidate even if the
before run fails. All product code remains unchanged after that tested revision.

| Check | Result |
| --- | --- |
| Exact public1374 base, identical story/data | 1/1 passed: expected absence of quotes/previews |
| Candidate browser | 8/8 passed: mounted quote story plus7 existing Home controls |
| Source/model/local join | 11 new tests passed;25 prerequisite tests passed |
| Existing feed/profile validators | 17 feed +25 profile tests passed |
| Frontend typecheck | Passed |
| App capture/npm/SDK verifier | 698 objects verified |
| Progress verification | Current progress checked;9 controls passed |
| Required repository checks | 9 captures verified;10 tooling tests passed |

The before run's passing expected-absence assertions are not an observed failing
test. The candidate measured three original-style `BLOCKQUOTE` previews, exact
recorded quote ordering/text, unchanged root records/counts, root profile
keyboard navigation, and no horizontal overflow at1280/375px. No authored HTTP
fixture is substituted. Actual Next Home/profile reads returned200. Browser
mutation and nonlocal requests are blocked by the story.

Known React script-tag warnings appeared in the existing excluded404-route
controls and are preserved in the raw log. No blanket console-clean claim is
made for every route. The mobile full-page screenshot retains the existing
fixed-navigation overlay limitation. No all-pixel unobstructed, hit-test or
original pixel-identity claim follows from the width checks. Unavailable quote
states are source/model/join-tested, not browser-observed in this seed. No complete
browser-suite pass, real service, authenticated workflow, original
API/feature/milestone or translation qualification is claimed.

## Independent production qualification

The root agent subsequently checked the exact public head
`8746f593b21fd02a727cf824fd5bbbbbe5e5de6c` with the ordinary `pnpm build`
(SDK, backend, Next production build), recursive `pnpm typecheck`, app evidence
verification and progress plus9 tests. All four commands exited0.
[ROOT-PRODUCTION.json](ROOT-PRODUCTION.json) binds the tested tree, exact raw
checks record, four losslessly compressed logs and hashes of seven build
manifests retained privately by the root agent. The actual no-cache notice and
bigint native-binding fallback remain in the build log.

The subsequent update appends these receipts only. Product, harness, source,
capture, SDK and prerequisite files remain identical to the tested public
head. The earlier eight-case browser proof and its finite limits are unchanged;
no runtime rerun or broader visual/behavior qualification is claimed.

- [Before](proof/before-1280.png)
- [After, desktop](proof/after-1280.png)
- [After, mobile](proof/after-375.png)
- [Before raw log](proof/browser-baseline.log)
- [Candidate raw log](proof/browser-candidate.log)
- [Executed comparison controller](proof/compare-browser.py)

[MANIFEST.json](MANIFEST.json) binds the proof bytes. From this packet directory:

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
