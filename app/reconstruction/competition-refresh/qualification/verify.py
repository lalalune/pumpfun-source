#!/usr/bin/env python3
"""Verify the finite, separately bound real-clock page and lifecycle receipts."""
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP = HERE.parents[2]


def require(value, message):
    if not value:
        raise ValueError(message)


def data(root, name):
    path = root / name
    require(not path.is_symlink() and path.resolve().is_relative_to(root.resolve()), "Invalid path: " + name)
    return path.read_bytes()


def load(name):
    return json.loads(data(HERE, name))


def digest(value):
    return hashlib.sha256(value).hexdigest()


record = load("RECORD.json")
manifest = load("MANIFEST.json")
for name, pin in manifest["files"].items():
    value = data(HERE, name)
    require(len(value) == pin["bytes"] and digest(value) == pin["sha256"], "Receipt changed: " + name)
for name, pin in record["applicationInputs"].items():
    value = data(APP, name)
    blob = hashlib.sha1(b"blob " + str(len(value)).encode() + b"\0" + value).hexdigest()
    require(digest(value) == pin["sha256"] and blob == pin["gitBlob"], "Qualified input changed: " + name)

marker = b'test("actual foreground pause, error/Retry and unmount retain request ownership"'
before_harness = data(HERE, "fdaab-spec.mts.txt")
final_harness = data(APP, "tests/browser/competition-refresh.spec.mts")
require(before_harness.split(marker)[0] == final_harness.split(marker)[0], "Shared setup or first two cases changed")
require(digest(before_harness.split(marker)[0]) == record["harnessMapping"]["sharedSetupAndCadencePrefixSha256"], "Harness mapping changed")
before_log = gzip.decompress(data(HERE, "logs/browser-baseline.log.gz")).decode()
batch_log = gzip.decompress(data(HERE, "logs/browser-fixed.log.gz")).decode()
final_log = gzip.decompress(data(HERE, "logs/browser-fixed-lifecycle-final.log.gz")).decode()
require("2 failed" in before_log and 'Received: "$100.00"' in before_log and 'Received: "Synthetic read snapshot 1"' in before_log, "Causal baseline mismatch")
require("2 passed" in batch_log and "1 failed" in batch_log, "Initial fixed batch must retain its fixture failure")
require("1 passed" in final_log, "Final focused lifecycle did not pass")
for phase in ["baseline", "fixed"]:
    for kind, field, initial, changed, lower in [("detail", "pnlUsd", 100, 200, 14500), ("list", "title", "Synthetic read snapshot 1", "Synthetic read snapshot 2", 59500)]:
        observed = load(f"browser/{phase}/{kind}/observed.json")
        require(observed["realClock"] and not observed["unexpected"], "Unexpected browser capability")
        replies = [row for row in observed["responses"] if row.get("body", {}).get("ok")]
        def value(row):
            body = row["body"]["data"]
            return body["entries"][0][field] if kind == "detail" else body["live"][0][field]
        require(value(replies[0]) == initial, "Initial actual Next body changed")
        changed_body = load(f"browser/{phase}/{kind}/changed-backend-response.json")["data"]
        require((changed_body["entries"][0][field] if kind == "detail" else changed_body["live"][0][field]) == changed, "Actual changed backend response missing")
        if phase == "baseline":
            require(len(replies) == 1, "Baseline unexpectedly polled")
            require(observed["finishedAtMs"] - observed["startedAtMs"] >= lower, "Baseline real-clock wait missing")
        else:
            require(value(replies[1]) == changed, "Fixed Next response did not admit changed facts")
            require(replies[1]["atMs"] - replies[0]["atMs"] >= lower, "Real cadence gap is too short")

focus = load("browser/lifecycle-final/focus-states.json")
require(len(focus) == 3, "Missing real focus observations")
require(focus[0]["state"] == focus[1]["state"] == {"focused": False, "visibility": "visible"}, "Real blur/visibility precondition missing")
require(focus[2]["state"] == {"focused": True, "visibility": "visible"}, "Real foreground return missing")
require(focus[1]["atMs"] - focus[0]["atMs"] >= 17000, "Blur wait was not real elapsed time")
require(focus[0]["native"]["ledger"] == focus[1]["native"]["ledger"], "A read occurred while blurred")
lifecycle = load("browser/lifecycle-final/observed.json")
require(lifecycle["realClock"] and not lifecycle["unexpected"], "Lifecycle browser capability changed")
require([row["status"] for row in lifecycle["responses"]] == [200, 200, 502, 200], "Actual failure/recovery changed")
for phase in ["baseline", "fixed", "lifecycle-intermediate", "lifecycle-final"]:
    require(load(f"browser/{phase}/server-exit.json")["code"] == 0, "Owned Next did not exit cleanly")
require("tests 20" in gzip.decompress(data(HERE, "logs/focused-prebrowser.log.gz")).decode(), "Focused receipt missing")
require("Verified 698" in gzip.decompress(data(HERE, "logs/evidence-final.log.gz")).decode(), "Evidence receipt missing")
print(f"Verified {len(record['applicationInputs'])} selected Git-bound inputs and {len(manifest['files'])} receipt files; 2 cadence passes plus 1 separately qualified lifecycle pass")
