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
    require(row["errors"] == [] and row["overflow"] <= 1, "page error/overflow changed")
    require(row["initial"]["focused"] == ["feed.beta"], "initial focus changed")
    for name in ["initialCenter", "changedCenter", "remountCenter"]:
        require(abs(row[name]["offset"]) < 6 and row[name]["scrollTop"] > 0,
                "native center geometry changed: " + name)
    require(row["sameTarget"]["scrollTop"] == 0 and row["sameTarget"]["focused"] == ["feed.beta"]
            and len(row["sameTarget"]["host"]["timers"]) == 1, "unrelated rerender repeated scroll/timer")
    require(row["changed"]["focused"] == ["feed.alpha"]
            and len(row["changed"]["host"]["timers"][0]["cleared"]) == 1, "target change cleanup changed")
    require(row["expired"]["focused"] == [] and row["elapsed"] >= 2400,
            "actual native timer did not expire")
    require(row["afterExpiry"]["focused"] == [] and len(row["afterExpiry"]["host"]["timers"]) == 3,
            "one-shot state incorrectly reset after expiry")
    require(row["remounted"]["focused"] == ["feed.beta"]
            and len(row["remounted"]["host"]["timers"][2]["cleared"]) == 1, "remount cleanup changed")
    require(row["hidden"]["host"]["active"] == []
            and len(row["hidden"]["host"]["timers"][3]["cleared"]) == 1, "unmount timer cleanup changed")
    require(row["afterUnmount"]["focused"] == []
            and row["afterUnmount"]["host"]["active"] == [], "settled unmount changed")
    timers = row["afterUnmount"]["host"]["timers"]
    require(len(timers) == 4 and all(timer["delay"] == 2500 for timer in timers)
            and [index for index, timer in enumerate(timers) if timer["fired"] is not None] == [1],
            "native timer ledger changed")
    require(row["emptyTarget"]["focused"] == []
            and len(row["emptyTarget"]["host"]["timers"]) == 4, "falsey target acquired a timer")
    require(row["final"]["focused"] == [] and row["final"]["host"]["active"] == [], "final cleanup changed")
checks = json.loads((HERE / "checks.json").read_text())
require(len(checks) == 6 and all(item["exit"] == 0 for item in checks), "fixed check results changed")
require(record["results"][:6] == checks and all(item["exit"] == 0 for item in record["results"]),
        "recorded results mismatch")
import re
for name, count in [("focused-final.tap", 16), ("browser-final.tap", 1)]:
    log = gzip.decompress((HERE / "logs" / (name + ".gz")).read_bytes()).decode()
    for label, value in [("tests", count), ("pass", count), ("fail", 0)]:
        require(re.search(r"(?m)^ℹ " + label + " " + str(value) + r"$", log), "final count changed")
print("Verified", len(record["inputs"]), "selected Git-bound executed inputs and", len(manifest["files"]),
      "receipts; complete original readonly focus/frames, finite native-clock/scroll proof only")
