"""Reuse four immutable public #1751 test tools; do not duplicate them in this PR."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess

HERE = Path(__file__).resolve().parent
APP = HERE.parents[1]
REPO = APP.parent

def require(value, message):
    if not value:
        raise SystemExit(message)

def digest(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "gitBlob": hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()}

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source-dir", type=Path, help="Optional existing #1751 app directory when its Git objects are unavailable")
parser.add_argument("--clean", action="store_true", help="Remove only matching untracked reference copies")
args = parser.parse_args()
pins = json.loads((HERE / "reference-pins.json").read_text())
for name, expected in pins["files"].items():
    require(name.startswith("tests/fixtures/rules-dismiss-") and Path(name).name in {
        "rules-dismiss-http.mjs", "rules-dismiss-next.mjs", "rules-dismiss-next-fetch.mjs", "rules-dismiss-server.mts"
    }, "Unexpected reference path")
    target = APP / name
    if args.clean:
        if target.exists():
            require(not target.is_symlink() and digest(target.read_bytes()) == expected, "Reference changed; refusing cleanup: " + name)
            tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "app/" + name], cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
            if not tracked:
                target.unlink()
        continue
    if args.source_dir:
        source = args.source_dir / name
        require(source.is_file() and not source.is_symlink(), "Missing regular reference source: " + str(source))
        data = source.read_bytes()
    else:
        result = subprocess.run(["git", "show", pins["commit"] + ":app/" + name], cwd=REPO, env={**os.environ, "GIT_NO_LAZY_FETCH": "1"}, capture_output=True)
        require(result.returncode == 0, "Public reference objects unavailable; supply an existing #1751 app checkout via --source-dir. No fetch/install is performed.")
        data = result.stdout
    require(digest(data) == expected, "Public reference hash mismatch: " + name)
    if target.exists():
        require(not target.is_symlink() and target.read_bytes() == data, "Refusing to overwrite different fixture: " + name)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
print("Cleaned" if args.clean else "Prepared", "four hash-bound #1751 reference tools; no source copies belong in this PR")
