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
require(observations["requests"] == [{"method": "GET", "url": path}
                                     for path in ["/", "/fixture.js"]] * 2, "owned GET ledger changed")
require([row["width"] for row in observations["results"]] == [390, 1280], "widths changed")
all_ids = ["feed.blueCard", "feed.other", "privacy.warning"]
for row in observations["results"]:
    require(row["errors"] == [] and row["overflow"] <= 1, "browser controls changed")
    require(row["initial"]["ids"] == all_ids and row["initial"]["groups"] == ["Feed", "Privacy"],
            "initial order changed")
    require(row["filtered"]["ids"] == ["feed.blueCard"]
            and row["filtered"]["host"]["mounted"]["feed.blueCard"]
            == row["initial"]["host"]["mounted"]["feed.blueCard"], "keyed identity changed")
    require(row["hidden"]["ids"] == [] and row["hidden"]["host"]["mounted"] == {},
            "hidden transition changed")
    require(row["restored"]["ids"] == ["feed.blueCard"]
            and row["restored"]["host"]["mounted"]["feed.blueCard"]
            != row["initial"]["host"]["mounted"]["feed.blueCard"], "restored lifetime changed")
    require(row["privacy"]["ids"] == ["privacy.warning"] and row["privacy"]["groups"] == ["Privacy"],
            "visible-section filtering changed")
    require(row["allAgain"]["ids"] == all_ids and row["allAgain"]["groups"] == ["Feed", "Privacy"],
            "restored group order changed")
    for phase in ["empty", "blank", "unmounted"]:
        require(row[phase]["ids"] == [] and row[phase]["host"]["mounted"] == {},
                "host cleanup changed: " + phase)
    require(row["identifier"]["ids"] == ["feed.blueCard"], "identifier transition changed")
focused = gzip.decompress((HERE / "logs/focused-final.tap.gz").read_bytes()).decode()
browser = gzip.decompress((HERE / "logs/browser-final.tap.gz").read_bytes()).decode()
require("tests 20" in focused and "pass 20" in focused and "fail 0" in focused, "focused counts changed")
require("tests 1" in browser and "pass 1" in browser and "fail 0" in browser, "browser counts changed")
print("Verified", len(record["inputs"]), "selected Git-bound executed inputs and", len(manifest["files"]),
      "receipts; complete source component, finite synthetic-host proof only")
