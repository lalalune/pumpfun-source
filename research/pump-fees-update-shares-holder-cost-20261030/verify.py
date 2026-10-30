#!/usr/bin/env python3
"""Independent re-check of this packet: replays all 100 points on both images.

usage (from the packet folder): python3 verify.py --images '{"original": p, "candidate": p}'
The pump and pump_amm CPI dependencies are read from <original>/../../pump{,_amm}/deployed.so
(the evidence/original layout). Exit 0 = every image hash and both runtime files match
byte for byte after the replay; 1 = any difference.
"""
import sys
sys.dont_write_bytecode = True
import argparse, gzip, json, pathlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import producer  # noqa: E402


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--images", required=True)
    a = p.parse_args()
    paths = producer.load_paths(a.images)
    rt = HERE / "runtime"
    rec_bytes = (rt / "receipts.jsonl.gz").read_bytes()
    rep_bytes = (rt / "report.json.gz").read_bytes()
    report = json.loads(gzip.decompress(rep_bytes))
    for n, want in report["image_sha256"].items():
        got = producer.sha(paths[n])
        if got != want:
            fail(f"{n} image sha256 {got} != report {want}")
    stored = [json.loads(l) for l in gzip.decompress(rec_bytes).splitlines()]
    if [r["case"] for r in stored] != json.loads(json.dumps(producer.cases())):
        fail("receipt case list differs from producer.cases()")
    rows, rep = producer.produce(paths, producer.cases())
    rows = json.loads(json.dumps(rows))
    bad = 0
    for old, new in zip(stored, rows):
        for side in ("original", "candidate"):
            if old[side] != new[side]:
                bad += 1
                print(f"mismatch {old['case']['name']} on {side}: cu {old[side]['compute_units']} -> {new[side]['compute_units']}")
    if bad:
        fail(f"{bad} replayed points differ from the receipts")
    new_rec, new_rep = producer.encode(rows, rep)
    if new_rec != rec_bytes or new_rep != rep_bytes:
        fail("rebuilt runtime files differ")
    print(json.dumps({"ok": True, "points": report["point_count"], "behavior_mismatched": report["behavior_mismatched"],
                      "cu_mismatched": report["cu_mismatched"]}))
    sys.exit(0)


if __name__ == "__main__":
    main()
