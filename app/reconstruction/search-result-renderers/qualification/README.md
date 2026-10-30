# Frozen result-family qualification

Local source/method `925cb4081cf043c405141a972e0b818e551a3fbc` and public
source `f51809ff15fef16dc8937ddf7f68fd03f5e45776` share full source tree
`e1334861e66ba2cfcc96ba7c59076699bed11da1`. The later qualification commit
adds only this directory. There is no private-commit, original-workspace or
current-Git-head guard in the public replay commands.

From the repository root with existing pinned dependencies:

```sh
python3 app/reconstruction/search-result-renderers/qualification/verify.py
node app/scripts/original-search-result-renderers.mjs --check
node --test app/tests/original_search_result_renderers.test.mjs
node --test app/tests/original_search_result_renderers.browser.mjs
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
python3 app/scripts/verify-evidence.py
```

The read-only packet verifier hashes every sealed member and116 declared frozen
source/evidence inputs, plus15 actual bundled files and7 method inputs. Twelve
bundled files are the installed lock-pinned React/ReactDOM/scheduler dependencies.
An exported tree can supply `--dependency-root '/existing pinned app'` to read
those exact existing dependency bytes without an install/copy/cache. Normal Node
module resolution is required for the source checker. Paths are resolved from
the script, so invocation cwd and spaces in the exported root are supported.

The first frozen actual React/compiler/context story passes17 observations and
only two root/bundle GETs. It records the actual metadata/display field inputs,
provider-context/memo updates, mixed section visibility/loading/SeeAll, raw versus
projected group callback identity and trusted source click order. Its data,
renderer, classification, formatting, verification and navigation ports are
explicitly synthetic; this is not a real provider, service or product fixture.
The dispatcher asks its ordinary admission predicate and receives false; the
throwing deferred Perps display/row and menu action callbacks are never invoked.
All browser/server processes closed in finally; PRIMARY was explicitly released.

`MANIFEST.json` seals members except itself. The packet verifier checks integrity
only, not a signature, independent approval, security attestation or full
provider/application equivalence. These receipts do not transfer qualification
to #1925 or to a future composition. Existing captures, SDK, source helpers and
prior packages remain unchanged. No Next/full-app build, API/native/backend/
visual/accounting/feature-completion claim is made.
