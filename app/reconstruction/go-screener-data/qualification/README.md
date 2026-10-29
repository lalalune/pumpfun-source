# Offline source qualification

Measured local source `616242a9edd11a52e42358cd839ccf71a7577305` and public Git alias `720ae783037bae0c541b3ae3d41ec8a48d471446` have identical complete tree `19478c5609d8c24c32463729e8f06c230b0e776d`. Commit metadata differs. `SOURCE-INPUTS.json` binds all five new source/proof/doc/test files; the receipt followup only adds this qualification directory. It does not relabel a later source execution.

At that exact source: source verifier and **14 new focused cases PASS, 0 fail/skip**; application evidence **698 captures/npm integrity/unchanged SDK sources PASS**; generated progress plus **9 tests PASS**; required root **53 Git inputs /9 captures/10 tooling tests PASS**. The original root helper/export paths in its retained JSON are historical metadata, not public replay dependencies.

The first progress check failed because sparse checkout omitted three existing ledger-evidence files. `progress.log.gz` preserves that error, and `CHECKS.json` retains its exit1. `SPARSE-RESTORATION.json` records the exact measured-head Git blobs/SHA256/bytes restored without changing them. `RESTORED-CHECK.json` plus `progress-restored.log.gz` bind the subsequent exit0. No source/ledger/status/count changes were made to repair the sparse input set.

From a public checkout with the existing pinned dependencies and retained evidence:

```sh
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
cd app
node reconstruction/go-screener-data/verify.mjs --check
node --test tests/go_screener_data.test.mjs
python3 scripts/verify-evidence.py
python3 scripts/progress.py --check
python3 -m unittest discover -s tests -p test_progress.py
```

Every `.log.gz` is compressed text, not an executable archive. Read with stdlib `gzip` or `gzip -cd`; `MANIFEST.json` records retained lengths/SHA256. No private work files, local source alias or uncommitted fixture is required by these offline commands. No capture refresh/network/provider/account/API/Next/browser/binary execution is part of this qualification.

Original first-party `/go` HTML/Flight and same-origin assets bind the conditional main-app source chain. There was no `/go/bounties` route capture, observed lazy execution, anonymous API proof, server response/validation reconstruction, mounted UI/native behavior, feature/compatibility or security qualification. Tests use explicit synthetic parser/enrichment/query capabilities, never execute captured JavaScript, and do not claim actual Zod or service behavior.
