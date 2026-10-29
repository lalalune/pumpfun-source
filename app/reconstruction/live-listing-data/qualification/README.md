# Offline qualification

The measured local source is `ae1461c23035f14968baf9e7e8eae4bacb892af4`. Public Git alias `14af2d4483d02c5fc820315e794670d9293871ce` has the identical complete tree `728ff9bd2636a19df9599ff8e74470438619db41`; commit metadata differs. `SOURCE-INPUTS.json` binds every one of the five new reviewed files. The receipt followup only adds this qualification directory; it does not relabel a new execution.

At that exact source: source verifier PASS; **12 new focused tests PASS, 0 fail/skip**; app evidence verifies **698 captures, npm integrity and unchanged SDK sources**; generated progress and **9 tests PASS**; required root **9 captures/10 tooling tests PASS** against 53 authenticated Git inputs. The root helper's private export paths in the original receipt are historical execution metadata, not replay dependencies. From a full public checkout use the ordinary commands below.

The first progress check failed because sparse checkout omitted three existing ledger-evidence files. `progress.log.gz` preserves that failure. `SPARSE-RESTORATION.json` records their exact measured-head Git blobs, byte counts and SHA-256; restoring only those unmodified inputs yielded `progress-restored.log.gz`. The original failure and source are retained, with no ledger/status/count changes.

```sh
# repository root, with the repository's existing pinned dependencies
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
cd app
node reconstruction/live-listing-data/verify.mjs --check
node --test tests/live_listing_data.test.mjs
python3 scripts/verify-evidence.py
python3 scripts/progress.py --check
python3 -m unittest discover -s tests -p test_progress.py
```

All `.log.gz` files are compressed text, not executable archives. Read them with Python's stdlib gzip or `gzip -cd`; hashes/lengths are in `MANIFEST.json`. No private work files, local source alias, server, capture refresh or network request is required by these offline verification commands. A normal pinned dependency checkout and retained public capture/SDK inputs are required. No install, Next build, browser, live service, playback/provider, native/mounted feature, universal equivalence or security qualification is claimed.
