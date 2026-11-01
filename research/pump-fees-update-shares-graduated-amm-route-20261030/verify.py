#!/usr/bin/env python3
"""Independent re-check of this packet.

Run from the packet folder:
  python3 verify.py --images '{"original": "<pump_fees deployed.so>", "candidate": "<candidate.so>"}'

1. MANIFEST.json: every listed file exists with the recorded sha256 and size.
2. Image sha256 (both pump_fees images and the pump / pump_amm CPI
   dependencies) equal the values in runtime/report.json.gz. The
   dependencies are looked up as <root>/evidence/original/{pump,pump_amm}/deployed.so
   (--root, default two levels above this folder, i.e. the repo when the
   packet sits in research/) and, failing that, next to the original image
   (<original>/../../{pump,pump_amm}/deployed.so).
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


def dependency(prog, roots, original):
    tried = [pathlib.Path(r) / "evidence/original" / prog / "deployed.so" for r in roots]
    tried.append(pathlib.Path(original).resolve().parent.parent / prog / "deployed.so")
    for t in tried:
        if t.is_file():
            return str(t)
    fail(f"{prog} dependency image not found (tried {len(tried)} locations)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--images", required=True)
    p.add_argument("--root", default=None)
    a = p.parse_args()
    images = json.loads(a.images)
    roots = ([a.root] if a.root else []) + [str(HERE.parent.parent)]

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

    paths = {"original": images["original"], "candidate": images["candidate"],
             "pump": dependency("pump", roots, images["original"]),
             "pump_amm": dependency("pump_amm", roots, images["original"])}
    want = report["images_sha256"]
    for label, key in [("original", "original"), ("candidate", "candidate"),
                       ("pump_dependency", "pump"), ("pump_amm_dependency", "pump_amm")]:
        if producer.sha(paths[key]) != want[label]:
            fail(f"{label} sha256 differs from report")

    if [r["case"]["name"] for r in stored] != [c["name"] for c in producer.cases()]:
        fail("receipt case list differs from producer.cases()")
    if [r["case"] for r in stored] != json.loads(json.dumps(producer.cases())):
        fail("receipt case objects differ from producer.cases()")
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
            fail("behavior_match flag wrong: " + case["name"])
        if row["cu_match"] != ([s["compute_units"] for s in o] == [s["compute_units"] for s in c]):
            fail("cu_match flag wrong: " + case["name"])

    rebuilt = {
        "case_count": len(stored),
        "step_count": sum(len(r["original"]) for r in stored),
        "behavior_mismatch_cases": [r["case"]["name"] for r in stored if not r["behavior_match"]],
        "cu_mismatch_cases": [r["case"]["name"] for r in stored if not r["cu_match"]],
        "summary": json.loads(json.dumps(producer.summary(stored))),
    }
    for k, v in rebuilt.items():
        if report[k] != v:
            fail("report field differs: " + k)
    print(json.dumps({"verified_cases": len(stored), "steps": rebuilt["step_count"],
                      "behavior_mismatch_cases": rebuilt["behavior_mismatch_cases"],
                      "cu_mismatch_cases": rebuilt["cu_mismatch_cases"]}))
    sys.exit(0)


if __name__ == "__main__":
    main()
