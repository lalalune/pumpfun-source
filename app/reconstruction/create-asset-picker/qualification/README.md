# Finite picker qualification and public replay

This is an unmounted source reconstruction. Base
`094a06f18df738d41e77070c1a009e135671ac1a` has none of the eight new
picker/source/model/method paths. Actual archived callers and complete selected
functions are authenticated statically. The six cases use real React/compiler
with explicitly supplied capabilities, not a base-website/original-runtime
comparison or a working protected search service.

## Frozen/public mapping

Public source **`031b5c772c0a3ecac00ae878b624191be9000d1f`** and corrected
measured method **`8f784644b27de50591e5a3299e23d3733a87822b`** have identical
complete tree **`d1367afb21e747fe1d1f8b6bdcdd527ca95ba25e`**. All eight blobs
and SHA-256 values are in `VALIDATION.json`. Packet additions leave them
unchanged. Local IDs describe historical measurements; they are not claimed as
fetchable public ancestors.

The source verifier binds 38 physical roles/26 selected IDs,132 exact witnesses,
five complete selected components plus their invoked inline query,145 compiler
slots and actual default Create/coordinator/open-gateway caller witnesses.
Canonical UTF-8 is checked for client and contract. Original captures are
parsed, never executed. No loader/provider winner is inferred.

Thirteen frozen direct cases pass, including seven mutations rejected through
actual maintained `verify()`. They used source
`19ed54ed9ffabe3012b5e70fd14c05b295cd716a`; client, declarations, generator,
contract and tests are unchanged in the corrected/public source. The targeted
declaration typecheck, eleven shared-source checks,698 captured-object/npm
integrity checks,31 SDK-source checks and progress freshness/nine tests pass.
Source-stage mandatory root checks at corrected8f pass with53 authenticated
Git inputs,nine captures and ten tooling tests; raw record/logs retain that
actual revision. Final-public gates are reported separately on the PR.

## Initial failure and correction

The first real React method19ed passed **4**, failed **1** and left **1 unrun**.
The supplied translator read a global function without its own subscription.
When language changed, the source parent title/input updated, but its memoized
category child was not notified. The screenshot and trace show that exact
state. This is a synthetic-port limitation, not a reconstructed-source or
original-provider defect.

The exact sole correction was:

```diff
-useTranslation:()=>({t:state.t})
+useTranslation:()=>({t:usePorts().t})
```

Each supplied hook consumer now subscribes. Runtime client, controller/assertions,
timeouts, declarations, generator/contract and model cases are unchanged.
`fixture-19ed54.source.txt` and `controller-19ed54.source.txt` retain exact inert
old bytes, with Git/hash mappings and `translation-port-correction.patch`.
Both traces, both raw inputs/results/logs, the failure screenshot and both
losslessly compressed bundles remain. The initial shell printed the log after
Node, so its final shell status reflected `cat`; its explicit case5FAIL and
uncaught timeout are **not** counted as a passing run.

The corrected method passed **6/6**, not twelve unique cases. Both runs served
only `GET /` and `GET /bundle.js`, recorded no page errors or external attempts,
preserved all nineteen actual source/dependency input hashes, and closed their
browser and host. The two bundles differ because the fixture line differs.
For either stage, `gzip -dc browser-final/bundle.js.gz > /tmp/picker-bundle.js`
(or `browser-initial`) restores its exact original bytes; hashes are in the
result and validation record.

The six cases cover actual pending/local input/category/stock callbacks; a
supplied250ms timer hook with the complete source queryFn/normalizer and Pump
selection; hidden-category query admission; **in-memory**503 hook/error/report/
Retry/recovery; full raw-first eligibility selector and translated consumers;
trusted mouse/touch propagation, close callback and supplied subscription/timer
cleanup. No captured GET or telemetry provider executes. Shared art/avatar/name
and formatting ports use text/attributes, not media or financial calculation.

## Fetchable replay commands

Start in an existing repository checkout containing this packet and existing
pinned app dependencies (pnpm10.24). Babel parser/generator, React19.2.3/compiler,
frontend Playwright/Chromium and backend tsx/esbuild must already be installed.
This contribution did not install dependencies or change a lockfile. Preserve
all new replay output directories, including failed-run screenshots/traces.

```sh
git fetch --no-auto-maintenance --no-tags --filter=blob:none --depth=1 \
  https://github.com/shawkkkkk/pumpfun-source.git \
  031b5c772c0a3ecac00ae878b624191be9000d1f
git cat-file -e '031b5c772c0a3ecac00ae878b624191be9000d1f^{commit}'
node app/scripts/original-create-asset-picker.mjs --check
node --test app/tests/original_create_asset_picker.test.mjs
```

The same thirteen cases are expected, not another thirteen unique cases. From
`app`, the actual standalone React method is:

```sh
node reconstruction/create-asset-picker/qualification/browser.mjs \
  --source 031b5c772c0a3ecac00ae878b624191be9000d1f \
  --output "/tmp/create picker fresh React qualification"
```

The controller derives app/repository roots from its module URL and compares
four own actual runtime files to the requested Git commit before bundling.
It accepts the public source SHA; its guard was not removed. All bundled
inputs plus declarations/controller receive before/after hashes. It records
bundle, trace, input/result JSON and closes resources in `finally`. The host
uses a new ephemeral loopback port, GET-only HTML/bundle and restrictive CSP;
external browser requests are blocked. No Next process or original acquisition
starts. Never point `--output` at a retained historical directory.

Declaration check, from `app`:

```sh
corepack pnpm exec tsc --noEmit --strict --skipLibCheck --target ES2022 \
  --module NodeNext --moduleResolution NodeNext \
  reconstruction/create-asset-picker/client.d.mts
```

## Minimal public source/model export

`PUBLIC-EXPORT.json` authenticates **42** files from the fetchable public source:
eight new files, shared source helper, capture manifest/index, three already-main
search-session/search-client dependency files and28 raw captures. Code was copied
from exact Git bytes, immutable captures linked only after authentication and
existing dependencies used read-only. Source gate and the **same13** model cases
pass in the recorded path with spaces, with all inputs unchanged (not26unique).
No browser replay is claimed for this minimal export: it has no Git metadata.
The existing full checkout command above remains the real React replay method.

A fresh finite model export from this packet checkout is fully public:

```sh
python3 - <<'PY'
from pathlib import Path
import hashlib, json, subprocess
source = '031b5c772c0a3ecac00ae878b624191be9000d1f'
root = Path.cwd()
out = Path('/tmp/create picker public model export')
assert not out.exists(), 'choose a new output directory'
binding = json.loads((root / 'app/reconstruction/create-asset-picker/qualification/PUBLIC-EXPORT.json').read_text())
for entry in binding['files']:
    raw = subprocess.check_output(['git', 'show', source + ':' + entry['path']])
    assert hashlib.sha256(raw).hexdigest() == entry['sha256']
    assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == entry['gitBlob']
    dest = out / entry['path']
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
(out / 'app/node_modules').symlink_to(root / 'app/node_modules', target_is_directory=True)
for args in [
    ['node', 'app/scripts/original-create-asset-picker.mjs', '--check'],
    ['node', '--test', 'app/tests/original_create_asset_picker.test.mjs'],
]:
    subprocess.run(args, cwd=out, check=True)
for entry in binding['files']:
    assert hashlib.sha256((out / entry['path']).read_bytes()).hexdigest() == entry['sha256']
print('42 public inputs unchanged; preserve output directory:', out)
PY
```

No command needs the private measurement path in the historical binding.
`search-client/contract.json` is a real static import dependency of the
already-main normalizer module, not an executed service or new schema parser.
Its omission in the sparse checkout caused the first pre-freeze model import
failure; hydration restored exact Git bytes. `history/` preserves that failure,
the earlier129-witness passes, inert sealed intermediate producer/tests and
setup failures (wrong shared-test filename and missing progress-test input).
Those are not qualified final results or additional coverage. After exact Git
hydration, actual11 shared-reader and9 progress tests passed. Three additional
actual-caller witnesses were frozen before the final13-case132-witness run.
`MANIFEST.json` covers source/packet members and excludes itself.

## Limits

The query/debounce/provider/transport/renderer ports are authored. The supplied
query port applies select and forwards complete options; it does not implement
TanStack caching/automatic retry/cancellation. The supplied250ms hook is not the
original debounce implementation. Existing identity and mutating normalizer
are credited; no response-shape validation, asset eligibility, protected access
or provider trust is invented. Classification/zero-value quirks are preserved,
not endorsed as financial admission. The current file types are local structural
signatures, not original TypeScript or runtime validators.

There is no original factory execution, real service/media/provider request,
wallet/session/credential/cookie acquisition, private H, fee projection,
reservation/funding/upload/instruction/signing/transaction/submit, maintained
product mount, Next/full-app build, original DOM/visual/runtime parity,
current-asset/market guarantee, API/native compatibility, security clearance or
milestone claim. Original captures, SDK, dependencies and prior packets are
unchanged. See source README for prior-unit credit and exact excluded boundaries.
