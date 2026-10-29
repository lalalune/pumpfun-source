# Frozen local-settings qualification

Run from `app/`. Tested source and method:
`3e6abe66aed513eac9db5d396d242e06c0348790`.
19 domain and 11 shared-source tests pass, plus one real React browser workflow
at 390px and 1280px. Recursive typecheck, 698 capture/npm/SDK checks and nine
progress tests pass.
The final receipt commit changes only README and adds validation outputs;
executed source/generator/method/capture inputs remain Git-blob-identical.

Raw test/check logs are deterministically compressed. Browser observations and
two screenshots show the explicit synthetic host-control fixture, not the
product Settings page or original pixel identity. Source, strict canonical-byte
and original-AST verification is separate from the finite browser assertions.
No Next process, backend, actual browser storage/cookies, credentials or live
service is involved. The producer exits 0 after awaiting browser/server closure.

The prior precommit 19-test EXDEV fixture failure and precommit browser pass are separate
historical phases. Progress sparse-reference and wrong-cwd setup failures are
also retained; unchanged reference files were materialized and the normal app
command passes. No failed outcome is relabeled as a final-head pass.

    node scripts/original-local-settings-runtime.mjs
    python3 reconstruction/local-settings-runtime/validation/verify.py
    python3 -O reconstruction/local-settings-runtime/validation/verify.py

The receipt verifier checks 18 selected source, method, capture and package
bindings and saved observations. It does not rerun the workflow or provide an
independent compatibility oracle. No provider/API/full-app/financial/pixel,
server persistence, whole-registry, first-helper, security or milestone claim.
