# Qualification of the original balance-summary reader

Source revision: `e4dfd46291f9179b65bd9f51663b3e232288b466`, tree
`73d346080aefcecc9ae1e42af8d8e41855b95b38`, base
`094a06f18df738d41e77070c1a009e135671ac1a`. `VALIDATION.json` binds every source
blob and the actual checks; this packet is an additive documentation commit.
The later README qualification paragraph does not change the reader, verifier,
tests or generated source contract. Raw captures, reused source helper, existing
portfolio modules, SDK and product sources are unchanged.

Reproduce from an ordinary clone with the repository's existing pinned setup:

```sh
node app/scripts/original-balance-summary.mjs --check
node --test app/tests/original_source.test.mjs app/tests/original_balance_summary.test.mjs
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
cd app
python3 scripts/verify-evidence.py
python3 scripts/progress.py --check
python3 -m unittest discover -s tests -p test_progress.py
```

All returned zero. The focused log is 20/20. `http-workflow.json` is the actual
ordered synthetic loopback transcript: seven completed GET responses and one
aborted GET. It omits only the ephemeral origin, not status/body/path/query.
No live profile request, mutation, browser, credentials/session data, RPC, build,
original accounting/PnL, native compatibility or UI-completion claim is involved.

`mandatory-common-source.json` records the 46 actual read paths observed while
running the unchanged official root scripts against the source revision. Each
matches its recorded Git blob/SHA256. The read observer was a private provenance
diagnostic; normal public replay above requires neither it nor any private
commit/root/cwd guard. Historical observations are preserved as recorded and do
not transfer results to later combined application trees.

`before.json` proves only that these maintained implementation/verifier paths
were absent at the immutable base. No baseline server result is fabricated.
The initial author's one failed negative-zero expectation is disclosed in
`VALIDATION.json`; it was corrected to the source's actual -0 result without
changing the reader operation. Original React/query scheduling and provider/auth
behavior remain explicit capability boundaries; there is no full-app/Next pass.
