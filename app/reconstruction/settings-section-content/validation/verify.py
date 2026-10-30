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
prior = record["priorAttempt"]
changed = []
for name, entry in prior["inputs"].items():
    expected = subprocess.check_output(["git", "rev-parse", prior["revision"] + ":app/" + name],
                                       cwd=APP, env=env).decode().strip()
    data = subprocess.check_output(["git", "show", prior["revision"] + ":app/" + name], cwd=APP, env=env)
    require(expected == entry["gitBlob"] and blob(data) == expected and sha(data) == entry["sha256"],
            "prior phase binding changed")
    if entry != record["inputs"][name]:
        changed.append(name)
require(changed == prior["methodOnlyChange"] == ["tests/original_settings_section_content_browser.test.mjs"],
        "method/source mapping changed")
observations = json.loads((HERE / "browser/observations.json").read_text())
require(observations["bundleSha256"] == record["browserBundleSha256"], "bundle changed")
require(observations["requests"] == [{"method": "GET", "url": name}
                                     for name in ["/", "/fixture.js"]] * 2, "GET ledger changed")
require([row["width"] for row in observations["results"]] == [390, 1280], "widths changed")
for row in observations["results"]:
    require(row["errors"] == [] and row["overflow"] <= 1, "error/overflow changed")
    initial = row["initial"]
    require(initial["ids"] == ["chart.axis.synthetic", "chart.markers.b", "chart.markers.a"]
            and initial["compact"] == [None, "true", "true"], "initial order/compact changed")
    require(row["filtered"]["ids"] == ["chart.axis.synthetic", "chart.markers.b"], "filter changed")
    for key in row["filtered"]["ids"]:
        require(row["filtered"]["host"]["mounted"][key] == initial["host"]["mounted"][key],
                "retained key identity changed")
    require(row["restored"]["host"]["mounted"]["chart.markers.a"]
            != initial["host"]["mounted"]["chart.markers.a"], "restored field did not remount")
    require(row["emptyGroupRemoved"]["labels"] == ["unlabelled"], "empty group removal changed")
    require(row["feed"]["ids"] == ["feed.second", "feed.first"]
            and not set(row["feed"]["host"]["frames"]).intersection(initial["host"]["frames"]),
            "source-keyed parent section transition changed")
    require(row["privacy"]["ids"] == ["privacy.synthetic"] and row["emptyPrivacy"]["labels"] == [],
            "privacy nonempty/empty changed")
    for phase in ["account", "notifications", "unknown", "unmounted"]:
        require(row[phase]["ids"] == [] and row[phase]["labels"] == [], "special/empty changed")
    require(row["unmounted"]["host"]["mounted"] == {} and row["unmounted"]["host"]["frames"] == {},
            "diagnostic host cleanup changed")
checks = json.loads((HERE / "checks.json").read_text())
require(len(checks) == 6 and all(c["exit"] == 0 and c["revision"] == record["testedHead"] for c in checks),
        "final checks changed")
require(record["results"][:6] == checks and all(c["exit"] == 0 for c in record["results"]),
        "result mapping changed")
import re
for name, count in [("focused-final.tap", 19), ("browser-final.tap", 1)]:
    log = gzip.decompress((HERE / "logs" / (name + ".gz")).read_bytes()).decode()
    for label, value in [("tests", count), ("pass", count), ("fail", 0)]:
        require(re.search(r"(?m)^ℹ " + label + " " + str(value) + r"$", log), "final counts changed")
failed = gzip.decompress((HERE / "prior-attempt/browser.tap.gz").read_bytes()).decode()
require(re.search(r"(?m)^ℹ pass 0$", failed) and re.search(r"(?m)^ℹ fail 1$", failed)
        and "resolved to hidden" in failed and prior["browserExit"] == 1 and prior["bundleReceipt"] is None,
        "original failed attempt lost/relabeled")
print("Verified", len(record["inputs"]), "final and", len(prior["inputs"]), "prior selected Git-bound inputs,",
      len(manifest["files"]), "receipts; full readonly section display, finite source-port proof only")
