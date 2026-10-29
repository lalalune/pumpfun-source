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
require(observations["bundleSha256"] == record["browserBundleSha256"], "browser bundle changed")
require(observations["requests"] == [{"method": "GET", "url": name}
                                     for name in ["/", "/fixture.js"]] * 2, "owned GET ledger changed")
require([row["width"] for row in observations["results"]] == [390, 1280], "widths changed")
for row in observations["results"]:
    require(row["unexpectedErrors"] == [] and row["overflow"] <= 1, "unexpected error/overflow")
    require(row["expectedSyntheticRejection"] == ["SYNTHETIC prefetch capability rejection"],
            "expected rejection changed")
    require(not row["initial"]["sentinel"] and row["initial"]["requests"][0]["locale"] == "fr",
            "initial missing-sentinel/normalized-locale changed")
    require(row["initial"]["mounted"] == {}, "initial loading did not exclude Section")
    require(not row["completedAbsent"]["sentinel"] and len(row["completedAbsent"]["mounted"]) == 1,
            "attempt-complete with absent sentinel changed")
    require(set(row["completedAbsent"]["mounted"]) != set(row["changedSection"]["mounted"]),
            "section key lifetime changed")
    require(row["searched"]["mounted"] == {} and len(row["searched"]["requests"]) == 1,
            "results route/unnecessary request changed")
    ready = row["alreadyComplete"]
    require(not ready["sentinel"] and len(ready["requests"]) == 1
            and len([event for event in ready["events"] if event[0] == "exists"]) == 1,
            "ready state incorrectly reset on provider change")
    require(row["fallback"]["requests"][1]["locale"] == "en"
            and len(row["sameIdentity"]["requests"]) == 2, "default/same-provider language changed")
    require(row["changedProvider"]["requests"][2]["locale"] == "de", "provider replacement changed")
    require(row["staleCompletion"]["mounted"] == {}
            and len(row["currentCompletion"]["mounted"]) == 1
            and not row["currentCompletion"]["sentinel"], "cleanup/current completion changed")
    require(row["settledAfterUnmount"]["mounted"] == {}
            and row["settledAfterUnmount"]["contentRenders"] == row["hidden"]["contentRenders"],
            "settling after unmount rerendered host")
    require(row["initiallyReady"]["sentinel"] and len(row["initiallyReady"]["requests"]) == 4,
            "initial ready instance acquired resources")
    require(not row["rejected"]["sentinel"] and len(row["rejected"]["mounted"]) == 1
            and len(row["rejected"]["requests"]) == 5, "rejecting capability finally branch changed")
    require(row["unmounted"]["mounted"] == {}, "final unmount cleanup changed")
import re
for name, count in [("focused-final.tap", 17), ("browser-final.tap", 1)]:
    log = gzip.decompress((HERE / "logs" / (name + ".gz")).read_bytes()).decode()
    for label, value in [("tests", count), ("pass", count), ("fail", 0)]:
        require(re.search(r"(?m)^ℹ " + label + " " + str(value) + r"$", log), "final count changed")
require(all(result["exit"] == 0 for result in record["results"]), "recorded failed final producer")
print("Verified", len(record["inputs"]), "selected Git-bound executed inputs and", len(manifest["files"]),
      "receipts; complete source attempt/content/loading, finite synthetic-provider proof only")
