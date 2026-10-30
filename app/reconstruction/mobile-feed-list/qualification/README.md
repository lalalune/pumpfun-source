# Finite mobile feed-list qualification

Public source `414a042e33e6911405a5194e0721827010c57a9f` has the exact complete
tree `432e17480bf8470fcdf776b2812fb46d66441a14` measured at corrected local
method `c5e21453cf615ad59c8f3ef4c54baaa96e4d8982`. `VALIDATION.json` binds all
eight source/model/type/method files; this packet adds receipts only. Source
README prospective run wording is historical; the final result is **6/6 pass**.

Count labels are explicit:52 selected physical roles across28 numeric IDs;
these selected roles also have52 distinct factory hashes. The core163807 owner
is one variant at one raw origin. There are82 source witnesses and151 compiler
slots. This does not count all indexed origins as separate recovered owners or
identify an active provider/loader winner.

Eleven model cases pass, including seven actual maintained-verifier rejections.
They first ran with uncommitted new files: `MODEL-INPUTS.json` preserves five
actual source/type/test hashes, all verified byte-identical to the public source.
The later commit is a source binding, not a claim that it was the executed Git
head. The pinned10.24 declaration typecheck,11 shared tests,698 captured-object/
npm/31-SDK integrity, progress freshness +9 tests, and source-head mandatory
53-input/9-capture/10-tooling checks pass. Setup diagnostics are retained: a
repo-root corepack invocation selected the wrong pnpm and was rejected; correct
app-cwd invocation passed. Sparse test/probe metadata inputs were authenticated
from Git before hydration. No install, guard bypass or source repair was used.

The first frozen six-case method919afa passed0/failed1/left5unrun. Its CSS-free
fixture attached the actual empty skeleton but gave it no visual height, so a
visible wait timed out. Exactly one controller line was corrected to wait for
attachment while retaining the assertion of all six skeleton children. No
client, fixture, types, source verifier, CSS, timeout or other assertion changed.
Original controller/fixture bytes, patch, failure screenshot, raw log, INPUTS,
RESULT and trace are retained. The local initial commit is not claimed to be a
fetchable public ancestor; its controller is inert archival evidence.

The corrected run passes all six cases; all16 actual source/dependency hashes
remain unchanged during each run. Only the controller input differs between
methods. Both runs produced the literally identical bundle, retained once as
reversible `bundle.js.gz`; both raw RESULT records bind its SHA. There were only
two loopback GETs, no blocked external attempts/page errors, browser and host
closed, and the final source unmount removed every supplied-read subscription
and manual-scroll listener. JSON snapshots naturally omit undefined object
properties; actual source and controller assertions retain those optional-field
handoffs. The same six cases are not twelve unique cases.

This is real React/compiler with native supplied pending/pagination buttons.
Readers, flags, classifiers, opaque financial/gate projections and renderers are
explicit ports. Provider updates are local harness controls; scrollY/events are
a manual port, not real viewport scrolling or observer behavior. The source
delegates reveal/fetch callbacks; the ports do not implement original cache/
query scheduling, actual provider acquisition or financial policy. Production
banner/pagination/row UI is not substituted and claimed as qualified. No image,
external link, real wallet/auth, financial request/calculation/action or original
factory/parent component executes. No Next server is used.

## Public source/model replay

The actual minimal export used49 Git-authenticated files at a path containing
spaces and existing pinned dependencies read-only. Source verification and the
same eleven cases pass, not22 unique cases. `PUBLIC-EXPORT.json` lists each Git
blob, SHA-256 and byte count; all inputs remained unchanged. Its historical
absolute export path is informational and never consumed by the procedure below.

From an existing checkout with documented pinned dependencies, fetch the exact
public source without materializing unrelated repository content:

```sh
git -c gc.auto=0 -c maintenance.auto=false fetch --no-auto-maintenance \
  --no-tags --filter=blob:none --depth=1 \
  https://github.com/shawkkkkk/pumpfun-source.git \
  414a042e33e6911405a5194e0721827010c57a9f
```

From the final PR checkout root, choose a new output path and run:

```sh
python3 - "$PWD" "/tmp/mobile feed public model replay" <<'PY'
from pathlib import Path
import hashlib, json, subprocess, sys
repo, out = map(lambda x: Path(x).resolve(), sys.argv[1:])
packet = json.loads((repo / 'app/reconstruction/mobile-feed-list/qualification/PUBLIC-EXPORT.json').read_text())
source = packet['source']
assert source == '414a042e33e6911405a5194e0721827010c57a9f'
assert len(packet['files']) == 49 and not out.exists()
assert subprocess.check_output(['git', 'rev-parse', source + '^{tree}'], cwd=repo, text=True).strip() == packet['tree']
for row in packet['files']:
    oid = subprocess.check_output(['git', 'rev-parse', source + ':' + row['path']], cwd=repo, text=True).strip()
    assert oid == row['gitBlob']
    raw = subprocess.check_output(['git', 'cat-file', 'blob', oid], cwd=repo)
    assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
    assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == oid
    dest = out / row['path']
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
(out / 'app/node_modules').symlink_to(repo / 'app/node_modules', target_is_directory=True)
print(out)
PY
cd "/tmp/mobile feed public model replay"
node app/scripts/original-mobile-feed-list.mjs --check
node --test app/tests/original_mobile_feed_list.test.mjs
```

The source/model resolve roots from module locations. The explicit working
directory above is the minimal export root; it has no Git metadata and is not
claimed to replay the browser. Preserve its directory and redirected logs. The
historical export used authenticated immutable capture hardlinks rather than
byte copies; their contents are identical. No private commit, generated media
fixture or additional reconstruction runtime is required.

## Optional fresh browser replay

On the final PR Git checkout, whose frozen eight files match public source,
using the existing dependencies and Chromium:

```sh
cd app
node reconstruction/mobile-feed-list/qualification/browser.mjs \
  --source 414a042e33e6911405a5194e0721827010c57a9f \
  --output "/tmp/mobile feed new browser result"
```

The output directory must not exist. The controller derives app/repository
roots from its module path, retains its four-file Git source guard, chooses an
ephemeral loopback port and preserves INPUTS/RESULT/bundle/trace outputs in that
directory. Finally cleanup does not delete evidence. Preserve the Node exit
status when redirecting output. A future run is a new result, not a replacement
for either archived method; the additive packet needed no browser rerun.

No whole Home/provider/schema/financial correctness, active variant winner,
actual acquisition, account/auth/session/credentials/cookies, follow/mutation,
submit/upload/funding/signing/transaction, original visual/DOM/runtime/native API
parity, security approval or feature/milestone completion is claimed.
