# Retain capture manifest checkpoints

The maintained `app/scripts/capture.py` already names response bodies using both
a URL prefix and the full response-content SHA-256. Changed response bytes do
not overwrite an earlier body. Its ordinary successful rerun nevertheless
replaced `manifest.json` without retaining the previous manifest: response
headers, acquisition times and record bindings were lost. `--resume` also
discarded the original full batch manifest, despite preserving record times.

The capture CLI now keeps each completed manifest under
`evidence/web/manifests/<full-raw-SHA256>.json` before atomically changing the
selected `manifest.json` alias. It also preserves any preexisting legacy
manifest exactly. An existing archive at the same digest must contain identical
bytes; a mismatch stops alias replacement. Response-body names, acquisition,
discovery and authenticated resume reuse are unchanged. Existing response bodies and prior
checkpoints are never deleted.

The application verifier authenticates each history filename/digest and checks
all historical body references through the existing integrity/path checks. The
strict object inventory is now the union of current and authenticated historical
references: historical bodies remain referenced, while unrelated objects still
fail. SDK/npm/source integrity checks remain unchanged. With no history folder,
the current checked-in collection still verifies the same 698 objects.

Malformed prior metadata is retained as bytes, not silently repaired or treated
as valid. The verifier rejects it. A failed publication can leave newly acquired
objects/checkpoints while preserving the previous selected manifest; it does not
promise rollback of the whole acquisition or repair of an already corrupt tree.
Historical snapshots are not substituted into current discovery/source lookups.
These integrity checks do not establish crawl completion, freshness or truth of
an external service response.

## Same-input reproduction

Base: `094a06f18df738d41e77070c1a009e135671ac1a`; tested source commit:
`3241013787a36ca2da363de70d518bfa4387356f`.

From `app/`:

```sh
python3 -B -m unittest discover -s tests -p 'test_capture_snapshot_history.py' -v
python3 -B -m unittest discover -s tests -p 'test_capture*.py' -v
python3 -B -m unittest discover -s tests -p 'test_verify_evidence.py' -v
python3 -B scripts/verify-evidence.py
pnpm check:progress
```

The regression copies the exact maintained CLI and verifier into temporary
application roots and invokes their actual subprocess entrypoints. Ordinary
urllib HTTPS goes through a loopback-only CONNECT fixture; an ephemeral local
certificate is trusted only by those subprocesses. TLS verification remains
enabled. The fixture permits only read-only GETs for the CLI's two fixed host
names, terminates them locally and never forwards to an external host. No live
crawl, credentials, wallet/signing operation or captured JavaScript execution is
involved. The fixture needs `openssl`; the local runs have no skips. Unchanged
published SDK inputs are copied locally so the actual verifier still checks
npm integrity and every source file.

All four final cases fail on the base and pass after correction: fresh v1→v2
recapture, resume provenance, refusal to replace a mismatched archived checkpoint,
and preservation/rejection of malformed prior metadata. Both fresh captures
return 14/14 successful responses. Before, all 14 old bodies survive but their
manifest does not; after, both full manifests and every body survive. Resume
performs zero extra requests and keeps each original record acquisition time.
Negative controls still reject changed historical bodies, changed archive bytes,
validly named history with false body digests, and unreferenced files.

The complete capture target passes **42/42** and verifier target **2/2**, with
zero skips. Current application evidence passes all 698 objects/npm/SDK checks;
progress plus nine tests and the source commit's required nine-capture and
ten-tooling gates pass. `SOURCE-BINDING.json` hashes the before/after source and
unchanged capture functions. Raw compressed logs and the exact synthetic before
and after output trees are retained here, with tar-member hashes. Those fixture
archives are test evidence, never additional captured-site or reconstruction
credit; they contain no ephemeral TLS private key. Extract them only into a new
private directory, never over repository evidence.

The first progress attempt hit sparse-omitted tracked proof files; its negative
log and exact 16-file hydration receipt are retained. No validation or feature
ledger was relaxed. Open #1216/#1378 independently address asset discovery;
#1217 changes source-reader snapshots and #1588 the archived root RPC helper.
Their implementations and all prior evidence packages remain untouched.

The initial 7a3761b9 source-phase receipts are preserved. Final 013eb9c8 only
completes the isolated verifier fixture with the unchanged local SDK package
manifest and clarifies its copy boundary; production capture/verifier bytes are
identical. The final same-input baseline still fails 4/4; candidate passes 4/4 and
the full capture target passes 42/42 again. Their `*-final-sdk-input.log.gz`
receipts and exact final source binding are retained separately. Open #1359
independently adds SDK identity checks; that code is not included here.

A final record-shape supplement corrects the initial public d9011b30 verifier:
a correctly hash-named manifest containing a non-record string was skipped by
the inherited body loops. The new same-input check fails on that intermediate
source (one failure/three passes) and passes after explicit record admission.
Each archived record now needs a URL and either a body path or the capture
producer's exact `{url,error:string}` transport-failure shape. Ordinary failures
remain allowed; malformed history is rejected. Final 32410137 tests also fail
4/4 on the original 094a06f1 base and pass 4/4 after; full capture 42/42, verifier 2/2,
698-object evidence, progress and required root gates pass again. All earlier
logs remain phase-bound; the new raw negatives and results are additive.
