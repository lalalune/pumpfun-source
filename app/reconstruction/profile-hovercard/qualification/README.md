# Finite profile-hovercard qualification

Public source commit `71a2990d0d3f956412621988b59197cb0b5dd9e6` has the exact
complete tree `afb42d398032ead26298878caa243a8230e428a3` measured locally at
`267cfba6102d07cc26b442492627c7aa6a3db220`. The eight source/model/type/method
files are listed in `VALIDATION.json`; this packet adds receipts without changing
them. The source README's prospective browser paragraph is historical source,
not the final result. The final recorded result is **six of six cases passed**.

`browser-final/RESULT.json` records real React/compiler behavior through native
local buttons and all sixteen actual source/dependency hashes before/after.
Only `GET /` and `GET /bundle.js` occurred. There were no external attempts or
page errors, and both browser and loopback host closed. The trace and reversible
bundle gzip are retained. No Next server or service acquisition was involved.

All query, identity, verification, reader, schema, financial projection,
formatting, hover primitive, clock and clipboard capabilities are supplied
ports. Financial values are literal metadata. The query port records options
and invokes selected callbacks; it is not an original cache/scheduler. Manual
clock advancement checks the actual 30000/2000ms registration and callback
lifetime, not wall-clock timing. Hover delay arguments500/100 are passed through,
not implemented. X/Avatar metadata are text and attributes only. The source
caption interval is cleared on close/change/unmount; the source feedback timeout
is intentionally retained. The method observes that remaining timeout and then
performs separate host environment cleanup. No operator clipboard is accessed.

The twelve model cases also pass, with seven actual maintained-verifier mutation
rejections within one case. The initial actual twelve-case run passed two and
failed ten because the generated X-link assignment omitted its original `let`
declaration. The exact five uncommitted initial files, hashes, failed log and
source correction are inert history. The producer now derives and emits the
original parent declaration kind; canonical byte comparison enforces the used
statement. The model case and declaration type bytes are unchanged between the
initial failure and final source. Initial bytes are not claimed to be a public
ancestor or a qualified source. Intermediate source-selector diagnostics are
also retained separately; only the final94-witness source is qualified.

The pinned declaration typecheck, eleven shared reader tests,698-capture/npm/
31-SDK integrity, nine progress tests and source-head mandatory53-input/9-capture/
10-tooling gates passed. An empty `ports-types.log` is normal successful tsc
output. `progress.log` preserves the nine unittest results; successful freshness
stdout was returned to the command output, not redirected into that file.

## Public source/model replay

The actual public replay used a new path containing spaces,44 Git-authenticated
files and the existing pinned dependencies read-only. `PUBLIC-EXPORT.json`
records each Git blob, SHA-256 and byte count. Both canonical source check and
the same twelve cases passed; they are not twenty-four unique cases. No browser
replay is claimed for that minimal export, which deliberately has no Git metadata.

From an existing repository checkout with its documented pinned dependencies,
fetch the exact public source without checking out unrelated content:

```sh
git -c gc.auto=0 -c maintenance.auto=false fetch --no-auto-maintenance \
  --no-tags --filter=blob:none --depth=1 \
  https://github.com/shawkkkkk/pumpfun-source.git \
  71a2990d0d3f956412621988b59197cb0b5dd9e6
```

Run the following from the final PR checkout root, changing only the new output
path. It copies exactly the recorded public Git files, authenticates every blob
and SHA, and points at the existing dependency tree. No original script runs.
The private historical absolute export path in the receipt is not consumed.

```sh
python3 - "$PWD" "/tmp/profile hover public model replay" <<'PY'
from pathlib import Path
import hashlib, json, subprocess, sys
repo, out = map(lambda x: Path(x).resolve(), sys.argv[1:])
packet = json.loads((repo / 'app/reconstruction/profile-hovercard/qualification/PUBLIC-EXPORT.json').read_text())
source = packet['source']
assert source == '71a2990d0d3f956412621988b59197cb0b5dd9e6'
assert len(packet['files']) == 44 and not out.exists()
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
cd "/tmp/profile hover public model replay"
node app/scripts/original-profile-hovercard.mjs --check
node --test app/tests/original_profile_hovercard.test.mjs
```

The producer and model resolve their roots from their module locations; the
explicit working directory above is the minimal export root. Preserve this
output directory and any redirected test logs. The historical export used
authenticated immutable capture hardlinks instead of byte copies; contents and recorded Git/hash bindings are the same. There is no private commit,
working-directory guess, generated media fixture or additional reconstruction
runtime dependency.

## Optional fresh browser replay from the public checkout

The browser method requires a Git checkout and retains its exact source guard.
On the final PR checkout, whose frozen eight files match the public source,
with existing documented dependencies and Chromium:

```sh
cd app
node reconstruction/profile-hovercard/qualification/browser.mjs \
  --source 71a2990d0d3f956412621988b59197cb0b5dd9e6 \
  --output "/tmp/profile hover new browser result"
```

The output directory must not exist. The method derives app/repository roots
from its own module location, checks four runtime/method files against that
fetchable commit, selects its own loopback port, and preserves INPUTS/RESULT,
bundle and trace in the explicit output directory. Browser/host finally cleanup
does not delete that evidence. Retain the Node exit status when redirecting its
output. A future replay is a new result, not a replacement for this historical
six-case receipt. No fresh browser run was needed for the additive packet.

No original factory/provider execution, mounted MAIN/profile behavior,
financial/schema correctness or acquisition, auth/follow, current identity or
balance, actual clipboard, external media/link navigation, original native/API/
DOM/runtime parity, security approval or milestone completion is claimed.
