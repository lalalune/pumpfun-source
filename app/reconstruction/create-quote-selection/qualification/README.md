# Finite qualification and public replay

The source is an unmounted reconstruction of the complete selected Create quote
coordinator, not a new asset service or mounted Create form. On base
`094a06f18df738d41e77070c1a009e135671ac1a` these eight source/model/method
paths do not exist. No base website or original-runtime differential is claimed.
The actual archived caller and complete selected functions are authenticated
statically; authored ports supply the excluded capabilities.

## Exact revisions and preserved initial failure

Public source **`0f52159d20c38fd5fd793ec1d3cc659e62d87c93`** and corrected
measured local method **`795f2c1af134ccd11ac8493afebabccf0aa414f6`** have the
same complete tree **`09df46a533d3fb5337012de9aa61b51123e98760`**. The eight
exact Git blobs/SHA-256 values are in `VALIDATION.json`. Receipt additions do
not change them. Local IDs identify historical measurements, not a claim that
those commits are public ancestors.

The initial frozen method `fde74628e08239f43fe177059923f8a00f79be76`
passed six cases, failed case seven and did not run case eight. It read the
whole radio button's innerText, which included the synthetic Image port's
aria-hidden `◇` glyph: `◇SOL !== SOL`. The source has a separate label span
and the accessible name is SOL. The only correction was two assertions now
reading the exact SOL/USDC label descendants. This is an oracle correction,
not a product fix. No runtime, fixture, declarations, source verifier or timeout
changed. `initial-browser.source.txt` retains the exact old controller as inert
bytes; `label-oracle-correction.patch`, the raw failure log, trace, screenshot
and result remain available. The public blob/hash binding is explicit; replay
of the old local commit is not required.

The corrected method passed **8/8** real React/compiler cases. Both runs made
only `GET /` and `GET /bundle.js`, had no page errors or external attempts,
closed their browser/host and preserved all sixteen actual input hashes. The
initial and final bundle bytes are identical. `bundle.js.gz` losslessly retains
that shared bundle (original SHA-256
`61e66b9fd0bbabf37eba55b99c5e6c45091d623374591fa2a1d2906f202fd38d`);
`gzip -dc bundle.js.gz > /tmp/create-quote-bundle.js` restores it. Traces and the
failure screenshot are local synthetic-host evidence, not original-site media
or original visual parity.

## Public commands

Use an existing repository checkout containing this packet and the existing
pinned application dependency installation (pnpm 10.24). No dependency install
or lockfile change was performed for this unit. Babel parser/generator, React
19.2.3/compiler runtime, the backend's tsx/esbuild and the frontend's
Playwright/Chromium must already be available. Start in the repository root;
all output directories below must be new and should be kept after completion.

```sh
git fetch --no-auto-maintenance --no-tags --filter=blob:none --depth=1 \
  https://github.com/shawkkkkk/pumpfun-source.git \
  0f52159d20c38fd5fd793ec1d3cc659e62d87c93
git cat-file -e '0f52159d20c38fd5fd793ec1d3cc659e62d87c93^{commit}'
node app/scripts/original-create-quote-selection.mjs --check
node --test app/tests/original_create_quote_selection.test.mjs
```

These are the same eleven model cases, including seven mutations rejected by
actual maintained `verify()`. Repeating them does not create another eleven
unique cases. Canonical UTF-8 equality is checked for generated client and
contract; captures are parsed, not executed.

The finite real React method accepts the fetchable public source SHA. It
checks its four actual source files against that commit before bundling:

```sh
cd app
node reconstruction/create-quote-selection/qualification/browser.mjs \
  --source 0f52159d20c38fd5fd793ec1d3cc659e62d87c93 \
  --output "/tmp/create quote fresh React qualification"
```

The root is derived from the controller's module URL, independent of the shell
working directory. `--source` still checks exact Git bytes; it is not removed
or silently redirected. The host uses an ephemeral loopback port and blocks
external requests. It preserves `INPUTS.json`, `RESULT.json`, bundle and trace,
including after-run source/dependency hashes, and closes resources in `finally`.
Keep the entire output directory, including failure screenshots on a failed run.
No Next server, original query/picker/provider, media request or wallet runs.
Do not overwrite the retained historical outputs when replaying.

For declaration checking from `app`:

```sh
corepack pnpm exec tsc --noEmit --strict --skipLibCheck --target ES2022 \
  --module NodeNext --moduleResolution NodeNext \
  reconstruction/create-quote-selection/client.d.mts
```

## Minimal public source/model export

`PUBLIC-EXPORT.json` binds all **21** needed files to public-source Git blobs:
eight new files, shared source reader, capture manifest, module index and ten
raw captures. The recorded export used a directory with spaces, authenticated
every input from Git, copied code, linked authenticated immutable captures and
used existing dependencies read-only. Source verification and the **same eleven**
model cases passed there with all input bytes unchanged. This minimal export
has no Git metadata and is **not** the historical browser host or a browser
replay. A fresh model-only export can be reproduced from this packet checkout:

```sh
python3 - <<'PY'
from pathlib import Path
import hashlib, json, subprocess
source = '0f52159d20c38fd5fd793ec1d3cc659e62d87c93'
root = Path.cwd()
out = Path('/tmp/create quote public model export')
assert not out.exists(), 'choose a new output directory'
binding = json.loads((root / 'app/reconstruction/create-quote-selection/qualification/PUBLIC-EXPORT.json').read_text())
for entry in binding['files']:
    raw = subprocess.check_output(['git', 'show', source + ':' + entry['path']])
    assert hashlib.sha256(raw).hexdigest() == entry['sha256']
    assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == entry['gitBlob']
    target = out / entry['path']
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
(out / 'app/node_modules').symlink_to(root / 'app/node_modules', target_is_directory=True)
for args in [
    ['node', 'app/scripts/original-create-quote-selection.mjs', '--check'],
    ['node', '--test', 'app/tests/original_create_quote_selection.test.mjs'],
]:
    subprocess.run(args, cwd=out, check=True)
for entry in binding['files']:
    assert hashlib.sha256((out / entry['path']).read_bytes()).hexdigest() == entry['sha256']
print('21 public inputs unchanged; preserve output directory:', out)
PY
```

`public-source.log` and `public-model.log` are actual export results. Their
private export location in the binding records where that measurement ran;
none of the commands above needs that path or a private commit.

## Other finite gates and limits

The targeted typecheck, unchanged shared source-reader eleven cases, 698
captured-object/npm integrity checks and 31 SDK-source checks pass. Progress
freshness plus nine checks pass. Source-method mandatory root checks pass with
53 Git-authenticated inputs, nine captures and ten tooling tests; their raw
record/logs are retained. Final-public checks are separately reported on the PR,
not retroactively relabelled as the source-method run. `MANIFEST.json` covers
source and packet members and excludes itself.

The real React fixture uses synthetic bound-store/query/picker/translation,
Mayhem/fee-sharing facades and shared rendering primitives. The image glyph
makes no image request. Synthetic dialog notification buttons qualify the
callback, not original backdrop/keyboard/focus behavior. Empty/missing Pump
fields qualify the defensive callback, not the original search's eligibility.
The store setter and shallow-record identity observations apply to supplied
records; no real viewer, wallet, session, credential or cookie is acquired.

The actual stock query, large picker search body and private fee-sharing
initializer remain inert source witnesses. No private H, fee projection,
funding, upload, instruction, signing or submit executes. No original factory
execution, mounted website, full-app/Next build, original DOM/visual/runtime
parity, service/native compatibility, financial admission, security clearance
or milestone claim follows from this packet. Prior attribution is credited in
the source README; original captures/SDK/prior packets remain unchanged.
