# Create UTF-8 validation qualification

Production runtime: **f9086478732fef060d4d00935ff62a30cd85e93c**.
The form and validator bytes remain identical to that revision. The final
qualification adds a browser PNG-readiness assertion, an explicit source-namespace
binding, and these receipts; it changes no production runtime files.

`checks.json` binds the exact production and executed test/proof file hashes.
Logs are losslessly gzip-compressed with both raw and compressed hashes.
`gzip -dc browser-final.log.gz` displays the original final browser output.

Before: restore exact form and validator from `665499915f9caedcd38921d415a90f0606686398`.
New unreferenced source-proof/test files remain on disk, inert. The exact final
model cases report **four failures/two passes**, exit 1. The browser's first case
confirms a selected image and real PNG decoding before reaching the substantive
wrong-validity assertion: the 33-byte name is marked valid. The assertion remains
strict and the run stops there.

After: restore the two candidate files, then run from `packages/frontend` with
the retained temporary config copied beside `playwright.config.ts`:

```
CREATE_UTF8_PHASE=candidate corepack pnpm exec playwright test \
  --config playwright.create-utf8.tmp.ts --max-failures=1 \
  tests/create-utf8.spec.ts tests/create.spec.ts \
  tests/create-video.spec.ts tests/create-external-links.spec.ts
```

All **21 browser cases pass**: three new and 18 maintained cases. Exact byte caps,
error focus/counters, valid Unicode preservation, description's independent
code-unit limit, native input caps and editing/reset recovery are verified.
The six model cases plus authenticated source-contract test pass. Frontend types,
698-object/npm/31-SDK integrity, progress and nine progress tests pass. Source-head
root checks pass nine captures and ten tooling cases; exact final-head root
results are recorded in the PR after publication.

The before image is a viewport at the first failed name assertion; the after is
a full page after both invalid fields and submit. Both use 1280px viewport width,
but their action prefixes/vertical crops differ. They demonstrate the changed
field state, not matched production screenshots or original pixel parity.

No full production build, broad suite, live backend compatibility or security
clearance is claimed. The command uses pinned pnpm 10.24.0 with existing dependencies;
there is no installation, upload, SDK change, wallet signing or chain operation.
