# Frozen finite qualification

Measured runtime and complete browser method:
`97cfd20ba0ae95c342e86b2f56ae66b97bbd95be`.
Fetchable public source:
`1400529f208fb84f9104803986566861321da12b`.
Both complete trees are `e3fd425177cb7653104041db9992792e1116f1ba`.
All eight frozen files remain unchanged by this additive results packet.

Results:

- Source verifier: six roles, 38 witnesses, complete 39-slot control.
- Eight direct cases pass, including six actual maintained-gate mutation
  rejections. The source/model tests use synthetic renderer/store ports.
- Local structural port declarations pass the retained targeted TypeScript
  command; these are not recovered original TypeScript declarations.
- Six standalone real React/compiler browser cases pass, with zero page errors.
  Four runtime files match the frozen Git source before execution; all sixteen
  source/dependency inputs match again afterward. Chromium closes, the server
  stops listening, and the only recorded requests are the two loopback GETs.
- Unchanged shared-source checks pass eleven cases; evidence integrity verifies
  698 records, npm integrity and 31 unchanged SDK source files. Progress and its
  nine tests pass. Mandatory repository gates pass nine captures and ten tooling
  tests, with all 53 inputs authenticated against the measured Git source.
- A separate 17-file Git-authenticated public export in a directory with spaces
  passes the source verifier and the same eight direct cases. This is a
  portability repeat, not sixteen unique direct cases. All input hashes remain
  unchanged. The browser is not repeated or relabeled at the public commit.

`VALIDATION.json` maps exact commands/source hashes and each raw record.
`MANIFEST.json` seals the source/method and packet members except itself.
The actual generated browser bundle is retained as `browser/bundle.js.gz`;
decompression was checked byte-for-byte against the raw producer output and
its SHA-256 in the result record. Compression does not alter executable output.

## Replay the browser from public source

From a Git repository with the public source commit available, its four runtime
files unchanged and the existing pinned application dependencies provisioned:

```bash
git cat-file -e 1400529f208fb84f9104803986566861321da12b^{commit}
node app/reconstruction/create-advanced-fee/qualification/browser.mjs \
  --source 1400529f208fb84f9104803986566861321da12b \
  --output "/tmp/create fee public fresh run"
```

Choose a new output directory. The runner derives its root from its own module
path and checks actual runtime bytes against the requested Git commit. Public
commit metadata may differ from the historical local freeze; identical runtime
bytes are required. No private commit or historical absolute path is required.
The runner needs the existing app/frontend/backend dependency trees, because it
resolves pinned React/Playwright and esbuild from the installed workspace. It
never installs dependencies or starts Next. Source drift fails the guard.

## Minimal public source/model replay

The following Bash sequence reproduces the **source verifier and eight direct
cases**, using only the seventeen Git-authenticated files and a read-only link
to existing pinned app dependencies. It deliberately does not execute the
browser controller outside a Git checkout. Choose a new export location; all
outputs and logs remain on failure or success.

```bash
set -euo pipefail
REPO="$PWD"
SOURCE=1400529f208fb84f9104803986566861321da12b
EXPORT="${TMPDIR:-/tmp}/advanced creator fee public replay"
git cat-file -e "$SOURCE^{commit}"
test -d "$REPO/app/node_modules"
test ! -e "$EXPORT"
mkdir -p "$EXPORT"
while IFS= read -r relative; do
  mkdir -p "$EXPORT/$(dirname "$relative")"
  git show "$SOURCE:$relative" > "$EXPORT/$relative"
done <<'INPUTS'
app/scripts/original-contracts/source.mjs
app/scripts/original-create-advanced-fee.mjs
app/tests/original_create_advanced_fee.test.mjs
app/reconstruction/create-advanced-fee/client.mjs
app/reconstruction/create-advanced-fee/client.d.mts
app/reconstruction/create-advanced-fee/contract.json
app/reconstruction/create-advanced-fee/README.md
app/reconstruction/create-advanced-fee/qualification/browser.mjs
app/reconstruction/create-advanced-fee/qualification/fixture.mjs
app/evidence/web/manifest.json
app/recovered/modules.json
app/evidence/web/objects/89ce7de3b9bad421.js
app/evidence/web/objects/1147ad0a1bf513f9.js
app/evidence/web/objects/256f83f9b5d323e6.js
app/evidence/web/objects/fd402d4185b44ce9.js
app/evidence/web/objects/01ad4f413e529b60.js
app/evidence/web/objects/e01139c6299580b1.js
INPUTS
ln -s "$REPO/app/node_modules" "$EXPORT/app/node_modules"
(
  cd "$EXPORT"
  node app/scripts/original-create-advanced-fee.mjs --check > source.log 2>&1
  node --test app/tests/original_create_advanced_fee.test.mjs > focused.log 2>&1
)
```

Expected: six roles/38 witnesses/39 slots, eight passed, zero failed/skipped.
`public-export-inputs.json` records the exact Git blobs and SHA-256 values.
The actual export used independent copies for executable/source files and
immutable hardlinks for capture bytes; the commands above produce equivalent
file bytes without any donor path.

The browser exercises the reconstructed complete control with synthetic quote,
store, translator and renderer primitives. Its plain Input port forwards the
source attributes to a native input; native maxlength observations qualify that
port, not the original shared Input component. No original disclosure behavior,
wording, DOM/styling or provider timing is inferred. All fee projection and
submission consumers remain static; no HTTP service, fee/accounting engine,
wallet/session, signing, upload, transaction, website mount or milestone is
qualified.
