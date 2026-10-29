#!/usr/bin/env python3
"""Check the immutable finite receipt and its selected actual source inputs."""
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP = HERE.parents[2]
record = json.loads((HERE / "RECORD.json").read_text())
manifest = json.loads((HERE / "MANIFEST.json").read_text())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked(root, relative):
    path = root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Invalid receipt/input path: " + relative)
    return path.read_bytes()


for name, pin in manifest["files"].items():
    data = checked(HERE, name)
    assert len(data) == pin["bytes"] and digest(data) == pin["sha256"], name
for name, pin in record["applicationInputs"].items():
    data = checked(APP, name)
    assert digest(data) == pin["sha256"], name
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    assert blob == pin["gitBlob"], name

baseline = checked(HERE, "baseline-client.tsx.txt")
assert digest(baseline) == record["baseline"]["fileSha256"]
assert hashlib.sha1(b"blob " + str(len(baseline)).encode() + b"\0" + baseline).hexdigest() == record["baseline"]["gitBlob"]
before = gzip.decompress(checked(HERE, "logs/browser-baseline.log.gz")).decode()
after = gzip.decompress(checked(HERE, "logs/browser-fixed.log.gz")).decode()
assert "2 failed" in before and before.count('Received: "$100.00"') == 2
assert "3 passed (14.5s)" in after
assert "tests 15" in gzip.decompress(checked(HERE, "logs/focused-sealed.log.gz")).decode()
assert "fail 0" in gzip.decompress(checked(HERE, "logs/focused-sealed.log.gz")).decode()
assert "Verified 698" in gzip.decompress(checked(HERE, "logs/evidence-sealed.log.gz")).decode()
assert " 502 " in gzip.decompress(checked(HERE, "browser/fixed/next.log.gz")).decode()
for phase in ["baseline", "fixed"]:
    assert json.loads(checked(HERE, f"browser/{phase}/server-exit.json"))["code"] == 0
    ledger = json.loads(checked(HERE, f"browser/{phase}/requests.json"))["ledger"]
    assert ledger and all(row["keyMatched"] and row["method"] == "GET" and row["status"] == 200 for row in ledger)
    for width in [390, 1280]:
        body = json.loads(checked(HERE, f"browser/{phase}/{width}/realized-response.json"))
        assert body["ok"] and body["data"]["kind"] == "traders"
        alpha = next(row for row in body["data"]["entries"] if row["walletAddress"] == "11111111111111111111111111111112")
        assert alpha["pnlUsd"] == 100 and alpha["realizedPnlUsd"] == -20
fixed_ledger = json.loads(checked(HERE, "browser/fixed/requests.json"))["ledger"]
assert {row["generation"] for row in fixed_ledger} == {1, 2}
observed = json.loads(checked(HERE, "http-observed.json"))
assert observed["fixtureExitCode"] == 0
assert [row["status"] for row in observed["reads"]] == [401, 200, 200, 200, 400, 502, 200]
assert all(row["method"] == "GET" for row in observed["ledger"])
assert observed["ledger"][0]["status"] == 401 and not observed["ledger"][0]["keyMatched"]
print(f"Verified {len(record['applicationInputs'])} selected Git-bound application inputs and {len(manifest['files'])} finite receipt files; local synthetic workflow only")
