"""Check selected frozen inputs and retained finite React observations."""
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
    require(result.is_file(), "missing file: " + name)
    return result


record = json.loads((HERE / "RECORD.json").read_text())
manifest = json.loads((HERE / "MANIFEST.json").read_text())
actual = set()
for path in HERE.rglob("*"):
    require(not path.is_symlink(), "symlink receipt")
    if path.is_file() and path != HERE / "MANIFEST.json":
        actual.add(path.relative_to(HERE).as_posix())
require(actual == set(manifest["files"]), "receipt membership changed")
for name, entry in manifest["files"].items():
    data = safe(HERE, name).read_bytes()
    require(len(data) == entry["bytes"] and sha(data) == entry["sha256"], "receipt changed: " + name)
env = {**os.environ, "GIT_NO_LAZY_FETCH": "1"}
tree = subprocess.check_output(["git", "rev-parse", record["testedHead"] + "^{tree}"],
                               cwd=APP, env=env).decode().strip()
require(tree == record["testedTree"], "tested tree changed")
for name, entry in record["inputs"].items():
    expected = subprocess.check_output(["git", "rev-parse", record["testedHead"] + ":app/" + name],
                                       cwd=APP, env=env).decode().strip()
    require(expected == entry["gitBlob"], "Git binding changed: " + name)
    data = safe(APP, name).read_bytes()
    require(len(data) == entry["bytes"] and sha(data) == entry["sha256"]
            and blob(data) == entry["gitBlob"], "executed input changed: " + name)
observations = json.loads((HERE / "browser/observations.json").read_text())
require(observations["bundleSha256"] == record["browserBundleSha256"], "bundle changed")
require(observations["requests"] == [{"method": "GET", "url": name}
                                     for name in ["/", "/fixture.js"]] * 2, "owned GET ledger changed")
require([row["width"] for row in observations["results"]] == [390, 1280], "widths changed")
for row in observations["results"]:
    require(row["unexpectedErrors"] == [] and row["overflow"] <= 1, "unexpected error/overflow")
    require(row["expectedSyntheticSetterFailure"] == ["SYNTHETIC local setter denied"],
            "expected synthetic denial changed")
    require(len(row["initial"]["tokens"]) == 3 and len(row["initial"]["profiles"]) == 2,
            "initial synthetic values changed")
    require("synthetic-latest" in row["added"]["tokens"] and len(row["added"]["tokens"]) == 4,
            "synthetic latest addition changed")
    require(row["denied"]["tokens"] == row["added"]["tokens"], "denied write changed values")
    require("0xab" not in row["unhidden"]["tokens"]
            and "synthetic-latest" in row["unhidden"]["tokens"]
            and len(row["unhidden"]["tokens"]) == 3, "latest functional unhide changed")
    require(list(row["profileRemoved"]["profiles"]) == ["synthetic-alice"], "profile canonical deletion changed")
    require(row["tokensCleared"]["tokens"] == {} and len(row["tokensCleared"]["profiles"]) == 1,
            "per-list token clear changed")
    require(row["allCleared"]["tokens"] == {} and row["allCleared"]["profiles"] == {}, "final clear changed")
    writes = [event for event in row["allCleared"]["events"] if event[0] == "write-request"]
    require(len(writes) == 5 and sum(event[2] == "object" for event in writes) == 2,
            "callback functional/object shape changed")
    require(row["unmounted"]["tokens"] == {} and row["unmounted"]["profiles"] == {}, "unmounted values changed")
checks = json.loads((HERE / "checks.json").read_text())
require(len(checks) == 6 and all(item["exit"] == 0 for item in checks), "final checks changed")
require(record["results"][:6] == checks and all(item["exit"] == 0 for item in record["results"]),
        "record/check mapping changed")
import re
for name, count in [("focused-final.tap", 18), ("browser-final.tap", 1)]:
    log = gzip.decompress((HERE / "logs" / (name + ".gz")).read_bytes()).decode()
    for label, value in [("tests", count), ("pass", count), ("fail", 0)]:
        require(re.search(r"(?m)^ℹ " + label + " " + str(value) + r"$", log), "final counts changed")
prior = gzip.decompress((HERE / "logs/focused-development.tap.gz").read_bytes()).decode()
require(re.search(r"(?m)^ℹ pass 17$", prior) and re.search(r"(?m)^ℹ fail 1$", prior),
        "original fixture failure was lost or relabeled")
print("Verified", len(record["inputs"]), "selected Git-bound executed inputs and", len(manifest["files"]),
      "receipts; complete ordinary list/coerce/local-callback source, synthetic-port qualification only")
