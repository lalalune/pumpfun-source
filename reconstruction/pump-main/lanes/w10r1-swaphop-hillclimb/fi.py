#!/usr/bin/env python3
"""First-improvement variant of hc.py (builds are slow on the shared machine).

fi.py --wt WT --out OUT --base-score S --only m1,m2,... [--start ...] [--passes 2]
Evaluates the pool in order, `--workers` candidates at a time; the moment a candidate beats the
current point (equal size, zero losses, fewer slots_diff with ratio not lower, or equal slots and
higher ratio), it is accepted and the rest of the pool continues on top of it. Later passes retry
the mutations that were not accepted on the final point.
"""
import argparse, concurrent.futures as cf, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import hc


def better(r, cur):
    if not hc.ok(r) or r.get("so_sha") == cur.get("so_sha"):
        return False
    if r["ratio"] < cur["ratio"]:
        return False
    return hc.key(r) < hc.key(cur)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wt", required=True); ap.add_argument("--out", required=True); ap.add_argument("--base-score", required=True)
    ap.add_argument("--only", required=True); ap.add_argument("--start", default="")
    ap.add_argument("--module", default="mutations4"); ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--passes", type=int, default=2); ap.add_argument("--wid", type=int, default=0)
    a = ap.parse_args()
    mod = __import__(a.module)
    table = {mid: (o, n) for mid, o, n in mod.M}
    base_text = (Path(a.wt) / hc.REL).read_text()
    R = hc.Runner(a.wt, a.out, a.base_score, True)
    cur = [x for x in a.start.split(",") if x]
    cur_r = R.evaluate(a.wid, hc.apply(base_text, cur, table), cur)
    print("START", cur, cur_r.get("ratio"), cur_r.get("slots"), flush=True)
    pool = [x for x in a.only.split(",") if x and x not in cur]
    for p in range(a.passes):
        accepted_this_pass = False
        i = 0
        todo = [x for x in pool if x not in cur]
        while i < len(todo):
            batch = []
            while len(batch) < a.workers and i < len(todo):
                mid = todo[i]; i += 1
                t = hc.apply(base_text, cur + [mid], table)
                if t is not None:
                    batch.append((mid, t))
            if not batch:
                continue
            with cf.ThreadPoolExecutor(len(batch)) as ex:
                res = list(ex.map(lambda b: (b[0], R.evaluate(a.wid + batch.index(b), b[1], cur + [b[0]])), batch))
            for mid, r in res:
                print(f"  p{p} {mid:34s} {r['status']:14s} bytes={r.get('bytes')} slots={r.get('slots')} ratio={r.get('ratio')} "
                      f"loss={len(r.get('losses',[]))}/{len(r.get('raw_losses',[]))} {'SAME' if r.get('so_sha')==cur_r.get('so_sha') else ''}", flush=True)
            best = sorted([(hc.key(r), mid, r) for mid, r in res if better(r, cur_r)], key=lambda x: x[0])
            if best:
                cur.append(best[0][1]); cur_r = best[0][2]; accepted_this_pass = True
                print("ACCEPT", ",".join(cur), cur_r["ratio"], cur_r["slots"], flush=True)
        if not accepted_this_pass:
            break
    print("FINAL", ",".join(cur), cur_r.get("ratio"), cur_r.get("slots"), cur_r.get("bytes"), flush=True)


if __name__ == "__main__":
    main()
