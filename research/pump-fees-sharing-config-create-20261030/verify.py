#!/usr/bin/env python3
"""Independent re-check of this packet.

Run from the packet folder:
  python3 verify.py --images '{"original": "<pump_fees deployed.so>", "candidate": "<candidate.so>"}'

1. MANIFEST.json: every listed file exists with the recorded sha256 and size.
2. Image sha256 (both pump_fees images and the pump / pump_amm CPI
   dependencies) equal the values in runtime/report.json.gz. The dependencies
   are evidence/original/{pump,pump_amm}/deployed.so, found under --root if
   given, else under the first ancestor of this folder that has them, else
   next to the original pump_fees image (evidence/original/pump_fees/).
3. Every case stored in runtime/receipts.jsonl.gz is executed again on both
   images (the case object is read from the receipt) and every recorded step
   field, compute units included, must be equal.
4. The report counts and summary are rebuilt from the fresh rows and must be
   equal to the stored report.
Exit 0 on success, 1 on any difference.
"""
import argparse
import gzip
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent


def verify_manifest():
    """The packet pins every file it ships; check them before the producer runs."""
    manifest = json.loads((HERE / 'MANIFEST.json').read_text())
    # The loop below checks the files the manifest names; a file the packet ships
    # with no entry passes every check it makes. Compare the two sets first.
    manifest_paths = {entry['path'] for entry in manifest['files']}
    if len(manifest_paths) != len(manifest['files']):
        raise SystemExit('duplicate packet manifest path')
    entries = list(HERE.rglob('*'))
    # Python -B still reads cached bytecode; it must not bypass source admission.
    if any(p.is_symlink() or p.suffix in ('.pyc', '.pyo') for p in entries):
        raise SystemExit('packet contains a symlink or cached Python bytecode')
    packet_paths = {p.relative_to(HERE).as_posix() for p in entries
                    if p.is_file() and p != HERE / 'MANIFEST.json'
                    and p.name != '.DS_Store' and '.git' not in p.relative_to(HERE).parts}
    if manifest_paths != packet_paths:
        raise SystemExit('packet file set differs from MANIFEST.json: '
                         f'missing={sorted(packet_paths - manifest_paths)} '
                         f'extra={sorted(manifest_paths - packet_paths)}')

    for entry in manifest['files']:
        path = HERE / entry['path']
        data = path.read_bytes() if path.is_file() else None
        if (data is None or len(data) != entry['bytes']
                or hashlib.sha256(data).hexdigest() != entry['sha256']):
            raise SystemExit(f'packet member differs from MANIFEST.json: {entry["path"]}')


sys.dont_write_bytecode = True  # keep the packet folder free of __pycache__
sys.path.insert(0, str(HERE))
verify_manifest()
import producer  # noqa: E402  (packet file)


def fail(msg):
    print("FAIL:", msg)
    sys.exit(1)


def dependency_dir(root, original):
    tried = []
    if root:
        tried.append(pathlib.Path(root) / "evidence/original")
    tried += [p / "evidence/original" for p in HERE.parents]
    tried.append(pathlib.Path(original).resolve().parent.parent)
    for d in tried:
        if (d / "pump/deployed.so").is_file() and (d / "pump_amm/deployed.so").is_file():
            return d
    fail("pump / pump_amm dependency images not found (pass --root <repo>)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--images", required=True)
    p.add_argument("--root", default=None)
    a = p.parse_args()
    images = json.loads(a.images)

    manifest = json.loads((HERE / "MANIFEST.json").read_text())
    for f in manifest["files"]:
        data = (HERE / f["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != f["sha256"] or len(data) != f["bytes"]:
            fail("manifest mismatch: " + f["path"])

    report = json.loads(gzip.decompress((HERE / "runtime/report.json.gz").read_bytes()))
    receipts_text = gzip.decompress((HERE / "runtime/receipts.jsonl.gz").read_bytes()).decode()
    if hashlib.sha256(receipts_text.encode()).hexdigest() != report["receipts_sha256"]:
        fail("receipts sha256 differs from report")
    stored = [json.loads(line) for line in receipts_text.splitlines()]

    deps = dependency_dir(a.root, images["original"])
    paths = {"original": images["original"], "candidate": images["candidate"],
             "pump": str(deps / "pump/deployed.so"), "pump_amm": str(deps / "pump_amm/deployed.so")}
    want = report["images_sha256"]
    for label, key in [("original", "original"), ("candidate", "candidate"),
                       ("pump_dependency", "pump"), ("pump_amm_dependency", "pump_amm")]:
        if producer.sha(paths[key]) != want[label]:
            fail(f"{label} sha256 differs from report")

    if [r["case"]["name"] for r in stored] != [c["name"] for c in producer.cases()]:
        fail("receipt case list differs from producer.cases()")
    for row, case in zip(stored, producer.cases()):
        if row["case"] != json.loads(json.dumps(case)):
            fail("receipt case object differs from producer.cases(): " + case["name"])

    rows = []
    for row in stored:
        case = row["case"]
        o = json.loads(json.dumps(producer.run_case(paths, paths["original"], case)))
        c = json.loads(json.dumps(producer.run_case(paths, paths["candidate"], case)))
        if o != row["original"]:
            fail("original replay differs: " + case["name"])
        if c != row["candidate"]:
            fail("candidate replay differs: " + case["name"])
        diffs = [f"{so['step']}:{k}" for so, sc in zip(o, c) for k in producer.BEHAVIOR if so[k] != sc[k]]
        if len(o) != len(c):
            diffs.append("step_count")
        if diffs != row["diff"] or (not diffs) != row["behavior_match"]:
            fail("behavior_match / diff wrong: " + case["name"])
        if ([s["compute_units"] for s in o] == [s["compute_units"] for s in c]) != row["cu_match"]:
            fail("cu_match wrong: " + case["name"])
        rows.append(row)

    rebuilt = {
        "case_count": len(rows),
        "step_count": sum(len(r["original"]) for r in rows),
        "behavior_mismatch_cases": [r["case"]["name"] for r in rows if not r["behavior_match"]],
        "cu_mismatch_cases": [r["case"]["name"] for r in rows if not r["cu_match"]],
        "summary": json.loads(json.dumps(producer.summary(rows))),
    }
    for k, v in rebuilt.items():
        if report[k] != v:
            fail("report field differs: " + k)
    print(json.dumps({"verified_cases": len(rows), "steps": rebuilt["step_count"],
                      "behavior_mismatch_cases": rebuilt["behavior_mismatch_cases"],
                      "cu_mismatch_cases": rebuilt["cu_mismatch_cases"]}))
    sys.exit(0)


if __name__ == "__main__":
    main()
