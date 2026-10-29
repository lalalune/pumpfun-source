#!/usr/bin/env python3
"""Check retained finite browser receipts and source bindings; no network."""
import gzip
import hashlib
import json
from pathlib import Path

packet = Path(__file__).resolve().parent
root = packet.parents[2]
receipt = json.loads((packet / "RESULT.json").read_text())


def require(condition, message):
    if not condition:
        raise SystemExit(message)


for name, expected in receipt["artifactSha256"].items():
    require(hashlib.sha256((packet / name).read_bytes()).hexdigest() == expected,
            "Changed artifact: " + name)
for name, expected in receipt["sourceSha256"].items():
    require(hashlib.sha256((root / name).read_bytes()).hexdigest() == expected,
            "Changed tested source: " + name)
for phase, status, open_state in [("before", "failed", False), ("after", "passed", True)]:
    events = json.loads((packet / (phase + "-events.json")).read_text())
    require(len(events) == 2, "Expected two paired cases")
    for case in events:
        require(case["status"] == status, "Wrong paired result")
        observed = case["observed"]
        require(observed["open"] is open_state, "Wrong product open state")
        product = observed["events"]["auth"]
        require([(x["type"], x["target"]) for x in product[:3]] ==
                [("pointerdown", "BUTTON"), ("pointerup", "DIALOG"), ("click", "DIALOG")],
                "Missing actual button-to-backdrop sequence")
        require(all(x["trusted"] for x in product), "Untrusted product event")
        native = observed["events"]["native"]
        require(native[2]["type"] == "click" and native[2]["open"] is True,
                "Native aborted press did not stay open")
        require(any(x["type"] == "click" and x["open"] is False for x in native),
                "Native ordinary outside-dismissal support missing")
        require(all(x["trusted"] for x in native), "Untrusted native event")
        expected_calls = ["connect", "on", "off"] if phase == "before" else ["connect", "on"]
        require(observed["walletCalls"] == expected_calls, "Wrong provider-listener observation")
report = json.loads(gzip.decompress((packet / "controls-report.json.gz").read_bytes()))
require(report["stats"]["expected"] == 18 and report["stats"]["skipped"] == 7 and
        report["stats"]["unexpected"] == 0 and not report["errors"], "Wrong finite control result")
node = gzip.decompress((packet / "node-tests.log.gz").read_bytes()).decode()
require("pass 28" in node and "fail 0" in node, "Wrong Node result")
require(receipt["frontendTypecheck"]["exit"] == 0 and
        (packet / "typecheck.log").read_bytes() == b"", "Wrong typecheck receipt")
require("3 factories, 6 fragments" in (packet / "source-evidence.log").read_text(), "Source verifier missing")
require("Verified 698 captured objects" in (packet / "app-evidence.log").read_text(), "App evidence check missing")
print("PASS: paired trusted browser/native gestures, 18 product cases/7 skips, 28 Node cases and exact source/evidence bindings")
