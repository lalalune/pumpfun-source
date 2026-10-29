# Finite source and model qualification

Public source is `a1179bdadf84adeb643020a67eedeb637cab8bff`, identical full
tree `7733ff6d8c38b7d1a1a8fd898ffd7a8bf4d7c967` to measured local source
`17e6257554b146d7670ba6675e8b78b4d5659b1f`. Both use immutable main parent
`094a06f18df738d41e77070c1a009e135671ac1a`. Publication changes commit
metadata, not source bytes. The qualification follow-up adds only this note
and the receipt directory.

- Source verifier passes: both reader variants, four identity variants, actual
  renderer and used dependencies, 15 factory roles and55 AST witnesses.
- All14 focused cases pass, without retries/skips. They use the maintained
  model, real Promises and explicit synthetic ports. The original factories are
  parsed, never executed. No HTTP request is sent, including to loopback.
- The actual maintained verifier rejects three changed packets, noncanonical
  bytes, raw capture corruption and a resealed changed original reader.
  Canonical comparison uses exact UTF-8 Buffer equality, not reparsed JSON
  semantic equality.
- App evidence verifies698 objects, npm integrity and all31 unchanged SDK source
  files. Progress check and9 tests pass; no ledger or milestone changes.
- Exact public source mandatory gate passes53 authenticated inputs,9 original
  captures and10 tooling tests.
- A minimal public export replays `--check` and all14 tests from a path containing
  spaces and an unrelated working directory. All20 required source/capture
  inputs are authenticated to the public Git revision and remain byte-identical
  after execution. Dependencies are existing/read-only, not a new install.

[Complete finite logs and hashes](validation/MANIFEST.json) retain both the
initial source-equivalent run and the public-export replay as separate runs;
their counts are not added together. No production build, typecheck, browser,
Next process or original runtime test was needed or claimed for this unmounted
JavaScript model.

To reproduce from a clean checkout using the normal pinned dependencies and
retained captures:

```sh
git fetch --no-tags https://github.com/shawkkkkk/pumpfun-source.git a1179bdadf84adeb643020a67eedeb637cab8bff
git switch --detach FETCH_HEAD
cd app
node scripts/original-verified-profile.mjs --check
node --test tests/original_verified_profile.test.mjs
```

The source script derives `app` from its own file location. No private commit,
absolute private runner, provider configuration, session, generated media or
server is required. Redirect stdout/stderr to a new external directory when
preserving another run; do not replace these historical receipts. The maintained
`node --test tests/*.test.mjs` step includes the new test without package/workflow
changes.

Preparation initially lacked existing sparse-checkout captures needed by the
broader evidence/progress checks. Missing inputs were restored only after
Git-blob authentication; the final complete checks above then passed. Earlier
setup failures remain private and are not relabelled as behavior failures or
passes. No dependency was installed and no capture/source checkpoint was edited.

This establishes the bounded source/model behavior only. Query scheduling,
actual verification status, trust, provider/auth/backend policies, UI rendering,
native compatibility and feature credit remain unqualified.
