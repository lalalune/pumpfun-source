# Finite qualification and public replay

Measured local source: `bb760cea233e18d1dd5c5a17d65dcf46f6dcc9ad`.
Fetchable public source: `676820ca2b99380dd4dec6cf2ff5e323e5e5c9c3`.
Their complete Git tree is identical:
`2569d9f9d2c3fee6cf92fd77589a959cb4384448`.

The five files in `VALIDATION.json:frozenFiveFiles` include the client, source
producer, contract, focused tests and original package README. Qualification
files are additive; no source result is retargeted to different implementation
bytes. `MANIFEST.json` seals each packet member except itself.

The source verifier and 15 model cases pass at the measured source. Seven
mutations call the actual maintained verification gate. Existing shared-source
and video checks pass 13 cases, existing media checks pass two, and evidence
integrity verifies 698 records, npm integrity and 31 unchanged SDK source files.
Progress checks and nine tests pass. Both mandatory repository scripts pass:
nine captures and ten tooling tests, with their 53 inputs bound to Git.

A separate **13-file Git-authenticated public export**, in a directory with
spaces, passes the source verifier and the same 15 cases. This is a portability
repeat, not 30 distinct cases. All 13 input hashes remain unchanged afterward.
See `public-export-inputs.json`, `public-export-results.json` and their raw logs.
Code files were independent copies; only immutable captures were hardlinked.
The existing pinned dependency directory was linked read-only, with no install.

Three pre-restoration logs retain setup failures: a sparse branch switch had
removed eleven capture files. `completed-capture-closure.json` records their
exact Git and SHA-256 authentication before restoration. The same media,
evidence and progress commands then passed. No product changes resolved those
missing-input errors. The initial successful focused run remains private;
`focused-final-source.log` is the explicit frozen-source run.

## Concrete replay from public source

Use a repository containing the fetchable public source commit and the existing
pinned application dependencies. No historical local commit is required. Run
the following in Bash from that repository root. The temporary export and both
logs are preserved on success or failure; choose a new empty export location.

```bash
set -euo pipefail
REPO="$PWD"
SOURCE=676820ca2b99380dd4dec6cf2ff5e323e5e5c9c3
EXPORT="${TMPDIR:-/tmp}/create validation public replay"
git cat-file -e "$SOURCE^{commit}"
test -d "$REPO/app/node_modules"
test ! -e "$EXPORT"
mkdir -p "$EXPORT"
while IFS= read -r relative; do
  mkdir -p "$EXPORT/$(dirname "$relative")"
  git show "$SOURCE:$relative" > "$EXPORT/$relative"
done <<'INPUTS'
app/scripts/original-contracts/source.mjs
app/scripts/original-create-validation.mjs
app/tests/original_create_validation.test.mjs
app/reconstruction/create-validation/client.mjs
app/reconstruction/create-validation/contract.json
app/reconstruction/create-validation/README.md
app/evidence/web/manifest.json
app/recovered/modules.json
app/evidence/web/objects/89ce7de3b9bad421.js
app/evidence/web/objects/6a1606765ef3e83e.js
app/evidence/web/objects/230764f4d2b8c952.js
app/evidence/web/objects/92f43c917bbc50e2.js
app/evidence/web/objects/5e15667ed36cac85
INPUTS
ln -s "$REPO/app/node_modules" "$EXPORT/app/node_modules"
(
  cd "$EXPORT"
  node app/scripts/original-create-validation.mjs --check > source.log 2>&1
  node --test app/tests/original_create_validation.test.mjs > focused.log 2>&1
)
```

Expected: the verifier reports five factory roles, two callers, thirteen fields
and 54 witnesses; focused output reports 15 passed, zero failed/skipped. Compare
the thirteen exported files to the Git blob/SHA-256 entries in
`public-export-inputs.json`. The script and tests resolve their application root
from their own module locations; there is no private working-directory guard,
generated media fixture, remote download or unpublished code prerequisite.

This does not run captured modules, React, a browser, HTTP, actual wallet/session
providers, upload/submit code or transactions. No full application build,
original runtime/provider parity or UI/feature credit is inferred.
