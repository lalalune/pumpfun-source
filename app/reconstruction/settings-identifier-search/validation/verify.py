"""Check frozen phase bindings and finite observations; no browser rerun."""
from pathlib import Path
import gzip
import hashlib
import json
import os
import subprocess

HERE = Path(__file__).resolve().parent
APP = HERE.parents[2]


def require(value, reason):
    if not value:
        raise SystemExit(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def safe(root, name):
    parts = Path(name).parts
    require(parts and not Path(name).is_absolute() and ".." not in parts, "unsafe path")
    result = root
    for part in parts:
        result = result / part
        require(not result.is_symlink(), "symlink input/receipt")
    require(result.is_file(), "missing regular file: " + name)
    return result


env = {**os.environ, "GIT_NO_LAZY_FETCH": "1"}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=APP, env=env)


manifest = json.loads((HERE / "MANIFEST.json").read_text())
record = json.loads((HERE / "RECORD.json").read_text())
actual = set()
for path in HERE.rglob("*"):
    require(not path.is_symlink(), "symlink receipt")
    if path.is_file() and path != HERE / "MANIFEST.json":
        actual.add(path.relative_to(HERE).as_posix())
require(actual == set(manifest["files"]), "receipt membership changed")
for name, entry in manifest["files"].items():
    data = safe(HERE, name).read_bytes()
    require(len(data) == entry["bytes"] and sha(data) == entry["sha256"], "receipt changed: " + name)
for phase, entry in record["phases"].items():
    require(git("rev-parse", entry["head"] + "^{tree}").decode().strip() == entry["tree"],
            "phase tree changed: " + phase)
for name, phases in record["inputs"].items():
    for phase, entry in phases.items():
        head = record["phases"][phase]["head"]
        require(git("rev-parse", head + ":app/" + name).decode().strip() == entry["gitBlob"],
                "Git phase binding changed: " + name)
        data = git("cat-file", "blob", entry["gitBlob"])
        require(len(data) == entry["bytes"] and sha(data) == entry["sha256"], "phase bytes changed")
    data = safe(APP, name).read_bytes()
    entry = phases["qualified"]
    require(sha(data) == entry["sha256"] and blob(data) == entry["gitBlob"], "current input changed: " + name)
before = record["phases"]["before"]["head"]
candidate = record["phases"]["candidate"]["head"]
qualified = record["phases"]["qualified"]["head"]
target = "app/packages/frontend/src/components/settings/settings-model.ts"
config = "app/packages/frontend/playwright.settings-id.config.ts"
require(git("diff", "--numstat", before, candidate).decode().strip() == "1\t0\t" + target,
        "before/candidate change is no longer the sole product line")
require(git("diff", "--name-only", candidate, qualified).decode().splitlines() == [config],
        "qualified change is no longer test-config typing only")
erasure = json.loads((HERE / "CONFIG-TYPE-ERASURE.json").read_text())
emitted = (HERE / "config-emitted.js").read_bytes()
require(erasure["equal"] and sha(emitted) == erasure["beforeEmittedSha256"]
        == erasure["afterEmittedSha256"], "type-erasure output changed")
require(erasure["beforeSourceSha256"] == record["inputs"][config[4:]]["candidate"]["sha256"]
        and erasure["afterSourceSha256"] == record["inputs"][config[4:]]["qualified"]["sha256"],
        "type-erasure source binding changed")
method = "packages/frontend/tests/settings-identifier-search.spec.ts"
require(len({e["gitBlob"] for e in record["inputs"][method].values()}) == 1,
        "final browser spec changed across phases")
for phase in ["before", "fixed"]:
    for width in [390, 1280]:
        row = json.loads((HERE / f"browser/{phase}/observations-{width}.json").read_text())
        require(row["width"] == width and row["errors"] == row["blocked"] == [], "browser controls changed")
        require(row["overflow"] <= 1, "overflow control changed")
        checks = row["observations"]
        require([r["query"] for r in checks] == ["external links", "GróUP CHATS", "not-mapped-setting",
                                                "privacy.confirmExternalLinks", "privacy confirmExternalLinks"],
                "query sequence changed")
        require([r["rows"] for r in checks[:4]] == [["privacy.confirmExternalLinks"],
                                                   ["chat.allowGroupNotifications"], [], []],
                "negative/ordinary controls changed")
        require(checks[4]["rows"] == ([] if phase == "before" else ["privacy.confirmExternalLinks"]),
                "causal outcome changed")
        require(all(r["method"] in ["GET", "HEAD"] and r["status"] == 200 for r in row["reads"]),
                "HTTP observations changed")
        require(any(r["path"].startswith("/?settings=privacy") for r in row["reads"]),
                "actual page GET missing")
for name, expected in [("browser-before.log", "2 failed"), ("browser-fixed.log", "2 passed")]:
    text = gzip.decompress((HERE / "logs" / (name + ".gz")).read_bytes()).decode()
    require(expected in text, "raw browser outcome changed")
print("Verified", len(record["inputs"]), "selected phase-bound inputs and", len(manifest["files"]),
      "receipts; two causal failures → two passes, separate typing-only mapping")
