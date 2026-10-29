"""Verify retained finite receipts and selected inputs, without rerunning them."""
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
    require(not Path(name).is_absolute() and parts and ".." not in parts,
            "unsafe validation path")
    result = root
    for part in parts:
        result = result / part
        require(not result.is_symlink(), "symlink validation path")
    require(result.is_file(), "missing regular file: " + name)
    return result


manifest = json.loads((HERE / "MANIFEST.json").read_text())
record = json.loads((HERE / "RECORD.json").read_text())
actual = set()
for path in HERE.rglob("*"):
    require(not path.is_symlink(), "symlink in receipt package")
    if path.is_file() and path != HERE / "MANIFEST.json":
        actual.add(path.relative_to(HERE).as_posix())
require(actual == set(manifest["files"]), "receipt manifest membership changed")
for name, entry in manifest["files"].items():
    data = safe(HERE, name).read_bytes()
    require(len(data) == entry["bytes"] and sha(data) == entry["sha256"],
            "receipt changed: " + name)
env = {**os.environ, "GIT_NO_LAZY_FETCH": "1"}
tree = subprocess.check_output(
    ["git", "rev-parse", record["testedHead"] + "^{tree}"], cwd=APP, env=env,
).decode().strip()
require(tree == record["testedTree"], "tested tree binding changed")
for name, entry in record["inputs"].items():
    expected = subprocess.check_output(
        ["git", "rev-parse", record["testedHead"] + ":app/" + name], cwd=APP, env=env,
    ).decode().strip()
    require(expected == entry["gitBlob"], "Git binding changed: " + name)
    data = safe(APP, name).read_bytes()
    require(len(data) == entry["bytes"] and sha(data) == entry["sha256"]
            and blob(data) == entry["gitBlob"], "executed input changed: " + name)

observations = json.loads((HERE / "browser/observations.json").read_text())
require(observations["bundleSha256"] == record["browserBundleSha256"],
        "browser bundle binding changed")
require([row["width"] for row in observations["results"]] == [390, 1280],
        "widths changed")
require(observations["requests"] == [{"method": "GET", "url": path}
                                     for path in ["/", "/fixture.js"]] * 2,
        "owned GET-only host ledger changed")


def count(state, kind):
    return sum(entry[0] == kind for entry in state["calls"])


for row in observations["results"]:
    require(row["expectedErrors"] == ["synthetic layout cookie denied"]
            and row["overflow"] <= 1, "error/overflow controls changed")
    require(row["initial"]["cookieText"] == "" and row["initial"]["listeners"] == 1,
            "initial lifecycle changed")
    require(row["selected"]["cookieText"].startswith("home_feed_layout=grid;"),
            "selected synthetic value changed")
    calls = row["selected"]["calls"]
    require(next(i for i, entry in enumerate(calls) if entry[0] == "write:done")
            < next(i for i, entry in enumerate(calls) if entry[0] == "notify"),
            "write-before-notify order changed")
    for kind in ["write:done", "notify"]:
        require(count(row["repeated"], kind) == count(row["selected"], kind) + 1,
                "same-option write/notify changed")
    require(row["rejected"]["cookieText"] == row["external"]["cookieText"]
            and count(row["rejected"], "notify") == count(row["external"], "notify")
            and count(row["rejected"], "write:attempt")
            == count(row["external"], "write:attempt") + 1,
            "denied-writer observation changed")
    require(row["retry"]["cookieText"].startswith("home_feed_layout=grid;"),
            "retry observation changed")
    require(row["unmounted"]["listeners"] == row["afterUnmount"]["listeners"] == 0,
            "unmount subscription changed")
    for kind in ["read", "notify"]:
        require(count(row["unmounted"], kind) == count(row["afterUnmount"], kind),
                "after-unmount host observation changed")
    require(row["remounted"]["listeners"] == 1
            and row["remounted"]["cookieText"] == row["afterUnmount"]["cookieText"]
            and row["remounted"]["cookieText"].startswith("home_feed_layout=table;"),
            "new lifetime observation changed")
focused = gzip.decompress((HERE / "logs/focused-final.tap.gz").read_bytes()).decode()
browser = gzip.decompress((HERE / "logs/browser-final.tap.gz").read_bytes()).decode()
require("tests 24" in focused and "pass 24" in focused and "fail 0" in focused,
        "focused receipt counts changed")
require("tests 1" in browser and "pass 1" in browser and "fail 0" in browser,
        "browser receipt counts changed")
print("Verified", len(record["inputs"]), "selected Git-bound executed inputs and",
      len(manifest["files"]), "receipts; finite synthetic-host proof only")
