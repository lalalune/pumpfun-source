# Finite source and React/DOM qualification

The measured commits are local historical identities, not presumed fetchable
public commits. `methods/` retains their exact complete controller, fixture and
source-proof bytes as gzip files. `BROWSER-COHORTS.json` binds each original head,
input record, outcome and method digest. Raw traces and both failure screenshots
remain under `browser/`; no old observation is rewritten.

| Cohort | Actually executed | Outcome |
| --- | --- | --- |
| `a2c4b71210bdc208a2ab314f13e121dabce42c6f` | Cases 1–2 | 1 pass, case 2 timeout; later cases not run |
| `d3297e159fa29e3257bf7853642287597a9f9ec0` | Cases 1–3 | 2 pass, case 3 timeout; later cases not run |
| `c05727129adfa6667721195ca920a05490d49d0e` | Explicit continuation, cases 3–6 | 4 pass, 0 fail; first two not rerun |

Thus **six distinct interactions** have passing finite evidence, across two
method revisions. This is not six passes at a final head. The first run placed
the inactive click target off-screen, allowing Playwright's automatic scrolling
and the source's scrollend selection to participate; it did not isolate the
capture-only assertion. The revised fixture exposes cards for click-capture
checks and constrains geometry expressly for the later scroll check. The second
run supplied the fake player failure synchronously from a click, which also
provides a document gesture. The continuation supplies that explicit callback
outside a click, then observes recovery on a subsequent actual key event. No
original autoplay/provider timing is inferred and no timeout was increased.

`METHOD-MAPPING.json` verifies that the first two assertion callback bodies are
byte-identical between the geometry and continuation revisions. The fixture
changes only by adding one explicitly callable synthetic failure method, unused
by those first two checks; other ports, markup and recovered components remain
unchanged. Current source later strengthens the static parent/lazy-source proof
and narrows the final case label to synthetic-player release. Neither adds a new
runtime result. The older label's mention of DOM cleanup is limited to
source-bound cleanup bodies; no per-listener/observer count was measured.

All three runs record the bundle digest and every actual esbuild input before
launch, the exact controller/proof digests, installed runtime versions, requests,
page errors and cleanup. Every browser and ephemeral host stopped; all runs have
zero page errors and zero non-origin request attempts. Player, image, provider,
telemetry and navigation ports are explicitly synthetic. Raw media and provider
responses are absent because none were requested. The harness is not an app
route and uses authored geometry, without an original visual claim.

The five final source/portable/mutation cases plus eleven unchanged shared-reader
cases pass (`focused.log.gz`). `source.log.gz` records the actual source check.
When the seven lazy assets were added to source authentication, the minimal
temporary export initially omitted one required script; the explicit export
input list was corrected. The verifier was not weakened or made to use private
fallback inputs.

Replay current source from `app/` using the existing pinned dependencies:

```sh
node reconstruction/live-preview-flow/recover.mjs --check
node --test tests/live_preview_flow.test.mjs tests/original_source.test.mjs
node reconstruction/live-preview-flow/browser.mjs --output NEW_OUTPUT_DIRECTORY
```

The destination must not already exist. Public replay uses the maintained
controller/component files, raw captures and normal workspace dependencies,
without private `/workspace` files or access to a local measured Git commit.
A fresh run is a new observation; compare its declared input hashes rather than
substituting its outcome for any historical cohort. The optional `--from 3`
exists solely to make the recorded continuation explicit, not to count skipped
controls as passing.

No original service, player, auth/join, account action, native compatibility,
application mount, live truth, feature milestone, financial or security
qualification is claimed. Existing source/capture attribution remains intact.
