#!/usr/bin/env python3
"""Verify finite replay receipts and current source bindings; no network."""
import gzip
import hashlib
import json
from pathlib import Path

packet = Path(__file__).resolve().parent
root = packet.parents[2]
result = json.loads((packet / "RESULT.json").read_text())


def require(condition, description):
    if not condition:
        raise SystemExit(description)


for name, expected in result["artifactSha256"].items():
    actual = hashlib.sha256((packet / name).read_bytes()).hexdigest()
    require(actual == expected, "Changed artifact: " + name)
for name, binding in result["inputs"].items():
    actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
    require(actual == binding["afterSha256"], "Changed tested input: " + name)
before = json.loads((packet / "before-http.json").read_text())["observations"]
after = json.loads((packet / "after-http.json").read_text())["observations"]
require(len(before) == len(after) == 9, "Nine HTTP cases required")
require([x["name"] for x in before] == [x["name"] for x in after], "Case identity mismatch")
broken = {"plain-object", "plain-array", "plain-number", "plain-boolean"}
for old, new in zip(before, after):
    require(new["actualStatus"] == new["declaredStatus"] == 200, "Wrong fixed status")
    if old["name"] in broken:
        require(old["actualStatus"] == 500, "Missing base failure")
        require(new["actualContentType"] == "text/plain", "Lost recorded media type")
        json.loads(bytes(new["bytes"]).decode())
    else:
        require(old == new, "Changed working control: " + old["name"])
for name, markers in {
    "before-portable-tests.log.gz": ["pass 1", "fail 1"],
    "after-tests.log": ["pass 2", "fail 0"],
}.items():
    text = (gzip.decompress((packet / name).read_bytes()).decode()
            if name.endswith(".gz") else (packet / name).read_text())
    require(all(x in text for x in markers), "Wrong focused test result: " + name)
full = gzip.decompress((packet / "backend-all.log.gz").read_bytes()).decode()
require("tests 966" in full and "pass 966" in full and "fail 0" in full, "Incomplete backend run")
for name in ["backend-all-exit.json", "typecheck-exit.json"]:
    require(json.loads((packet / name).read_text())["exit"] == 0, "Failed command: " + name)
require("Verified 698 captured objects" in (packet / "app-evidence.log").read_text(), "Missing evidence check")
print("PASS: 9-case HTTP receipts, unchanged controls, 2 regression tests, 966 backend tests, typecheck, evidence and source bindings")
