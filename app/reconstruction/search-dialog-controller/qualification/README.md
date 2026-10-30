# Finite source/controller qualification

The actual source/method run is local `ad147f88d32bcbbc823ca926c46da18957461dc4`.
Its entire source tree `2f1a7603732b39035a09fcc42e0305eb2133163f` equals public
source commit `d84b50100cfcf0654319e2c483387dfc22fa13eb`. The later qualification
commit only adds this directory. The public replay commands do not require that
private local commit, an original workspace path or a Git checkout: all declared
source bytes are hashed in `inputs.json`. The final PR maps its exact public
head separately; no historical measurement is retargeted.

From the repository root, with pinned dependencies already available:

```sh
python3 app/reconstruction/search-dialog-controller/qualification/verify.py
node app/scripts/original-search-dialog-controller.mjs --check
node --test app/tests/original_search_dialog_controller.test.mjs
node --test app/tests/original_search_dialog_controller.browser.mjs
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
python3 app/scripts/verify-evidence.py
```

The packet verifier hashes all sealed members,120 declared frozen Git inputs,
16 actual bundled inputs and7 method inputs. Twelve bundled files are installed
React/ReactDOM/scheduler dependencies pinned by the lockfile. An exported source
tree may use `verify.py --dependency-root '/existing pinned app'` to read those
same dependency bytes without installing, copying or altering them. The source
checker needs that tree's usual Node module resolution to pinned dependencies.
All paths are resolved from the script location, not the invocation cwd.

The first frozen real React/compiler story passed with17 observations and two
root/bundle GETs only. `react-verification.json` records every observed callback,
state, provider-result gate and actual input hash. These are supplied synthetic
ports, not original providers, a backend fixture, a current service or product
browser proof. The script/server/browser were closed and PRIMARY released.
There was no Next build. No second runtime story is claimed.

Raw initial draft diagnostics are retained separately. The generator first
mistook a copied function declaration for an expression; it rejected the AST
before writing a client. The initial negative-test mirror omitted a capture
needed by the unchanged inherited navigator verifier. Both were corrected before
freezing. Their uncommitted script snapshots were not retained, so these logs are
historical diagnostics only, not exact-head baseline/behavior receipts.

`MANIFEST.json` seals this directory's members except itself. This is an integrity
check, not a signature, security attestation, independent approval or whole
application/provider/feature qualification. Existing captures and earlier
packages remain unchanged.
