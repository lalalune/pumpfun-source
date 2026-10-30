#!/usr/bin/env python3
"""Greedy equal-size mutation hill-climb for swap_hop (wave 10; driver adapted from w7r1-swaphop-hillclimb).

hc.py --wt <worktree> --out <lane out> --base-score <score.json> [--module mutations4]
      [--workers 2] [--rounds N] [--start m1,m2] [--only m1,m2] [--prune] [--no-ledger]

Candidate = worktree multi_hop_curve_swap.rs + a list of mutations (line-preserving respellings).
Build: fastbuild.py (shared build-slot locks honoured by fastbuild itself) on a private crate copy
per worker. Measure: target_metric.py (bytes, ratio, slots_diff, calls) and score.py against the
base score.json (any normalized or raw loss rejects).
Fitness: equal original size (18,584 B) and zero losses required; then fewer slots_diff, then
higher ratio. A candidate is accepted only if it is no worse on either metric beyond --tol on
ratio (so slot gains cannot hide a ratio collapse).
Each trial is recorded in the shared ledger (dedupe key from the sorted mutation set).
Results are cached by source sha256 in <out>/hc/results.jsonl.
"""
import argparse, concurrent.futures as cf, hashlib, json, queue, shutil, subprocess, sys, threading, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
REL = "programs/pump/src/multi_hop_curve_swap.rs"
WIN = "0x5b3b0"
SYM = r"multi_hop_curve::swap_hop$"
ORIG_BYTES = 18584
LANE = "w10r1-swaphop-hillclimb"
BASE_TAG = "fw581362"


def apply(text, muts, table):
    for mid in muts:
        if mid not in table:
            return None
        old, new = table[mid]
        pairs = list(zip(old, new)) if isinstance(old, tuple) else [(old, new)]
        for o, n in pairs:
            if text.count(o) != 1:
                return None
            text = text.replace(o, n)
    return text


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def key(r):
    return (r["slots"] if r.get("slots") is not None else 10**9, -r["ratio"])


class Runner:
    def __init__(s, wt, out, base_score, ledger):
        s.wt, s.out, s.base_score, s.ledger = Path(wt), Path(out), base_score, ledger
        s.h = s.wt / "reconstruction/harness"
        s.hc = s.out / "hc"; s.hc.mkdir(parents=True, exist_ok=True)
        s.cache_path = s.hc / "results.jsonl"
        s.cache = {}
        s.lock = threading.Lock()
        if s.cache_path.exists():
            for l in s.cache_path.read_text().splitlines():
                d = json.loads(l); s.cache[d["sha"]] = d

    def prep(s, w):
        src = s.hc / f"src{w}"
        if not src.exists():
            shutil.copytree(s.wt / "programs/pump", src)
        return src

    def record(s, r, muts):
        if not s.ledger or not muts:
            return
        dk = f"{WIN}-{BASE_TAG}-hc10-{'+'.join(sorted(muts))}-v1"
        if len(dk) > 200:
            dk = f"{WIN}-{BASE_TAG}-hc10-sha{hashlib.sha1('+'.join(sorted(muts)).encode()).hexdigest()[:12]}-v1"
        st = r["status"]
        if st == "built":
            st = "rejected" if (r["losses"] or r["raw_losses"] or r["bytes"] != ORIG_BYTES) else "built"
        data = {"output": r.get("out", ""), "normalized": r.get("normalized"), "raw": r.get("raw"),
                "gains": r.get("gains", []), "losses": r.get("losses", []) + r.get("raw_losses", []),
                "target": {"slots_diff": r.get("slots"), "ratio": r.get("ratio"), "cand_bytes": r.get("bytes")},
                "notes": f"hill-climb on x1-p2 base (581362582 + main); so_sha={str(r.get('so_sha'))[:16]}"}
        run([sys.executable, str(s.wt / "reconstruction/pump-main/log_attempt.py"), "record", "--lane", LANE,
             "--approach", "hillclimb", "--target", WIN, "--dedupe-key", dk,
             "--hypothesis", "equal-size spelling hill-climb: " + "+".join(muts), "--status", st, "--data", json.dumps(data)])

    def evaluate(s, w, text, muts):
        label = "+".join(muts) or "base"
        sha = hashlib.sha256(text.encode()).hexdigest()
        if sha in s.cache:
            return s.cache[sha]
        src = s.prep(w)
        (src / "src/multi_hop_curve_swap.rs").write_text(text)
        o = s.hc / "o" / sha[:12]
        t0 = time.time()
        for attempt in range(5):
            b = run([sys.executable, str(s.h / "fastbuild.py"), "--src", str(src), "--work", str(s.out / f"work{w}"), "--out", str(o)])
            log = b.stdout + b.stderr
            if (o / "unstripped.so").exists() or "error[" in log or "error:" in log and "could not compile" in log:
                break
            if any(x in log for x in ("Too many open files", "ENFILE", "cannot lock ref", "Resource temporarily")):
                time.sleep(60)
            else:
                break
        so = o / "unstripped.so"
        r = {"sha": sha, "label": label, "secs": round(time.time() - t0, 1), "out": str(o)}
        if not so.exists():
            err = [l for l in log.splitlines() if "error" in l][:4]
            r.update(status="compile-failed", err=err)
        else:
            tm = run([sys.executable, str(s.h / "target_metric.py"), str(so), WIN, "--sym", SYM, "--top", "1"])
            t = json.loads(tm.stdout.strip().splitlines()[0])
            sc = run([sys.executable, str(s.h / "score.py"), str(so), "--baseline", s.base_score, "--json", str(o / "score.json"), "--quiet"])
            sd = json.loads(sc.stdout.strip().splitlines()[-1])
            r.update(status="built", ratio=t["ratio"], bytes=t["cand_bytes"], slots=t.get("slots_diff"),
                     calls=t["calls_candidate"], normalized=sd["normalized"], raw=sd["raw"], gains=sd["gains"],
                     losses=sd["losses"], raw_gains=sd["raw_gains"], raw_losses=sd["raw_losses"],
                     so_sha=sd["candidate_sha256"])
            for f in o.iterdir():
                if f.name not in ("unstripped.so", "score.json"):
                    shutil.rmtree(f, ignore_errors=True) if f.is_dir() else f.unlink()
        with s.lock:
            with open(s.cache_path, "a") as f:
                f.write(json.dumps(r) + "\n")
            s.cache[sha] = r
        s.record(r, muts)
        return r


def ok(r):
    return r["status"] == "built" and not r["losses"] and not r["raw_losses"] and r["bytes"] == ORIG_BYTES


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wt", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--base-score", required=True)
    ap.add_argument("--workers", type=int, default=2); ap.add_argument("--rounds", type=int, default=6)
    ap.add_argument("--start", default=""); ap.add_argument("--only", default="")
    ap.add_argument("--module", default="mutations4")
    ap.add_argument("--tol", type=float, default=0.0)
    ap.add_argument("--prune", action="store_true", help="drop mutations whose round-1 result was byte-identical or not ok")
    ap.add_argument("--no-ledger", action="store_true")
    a = ap.parse_args()
    mod = __import__(a.module)
    table = {mid: (o, n) for mid, o, n in mod.M}
    base_text = (Path(a.wt) / REL).read_text()
    R = Runner(a.wt, a.out, a.base_score, not a.no_ledger)
    cur = [x for x in a.start.split(",") if x]
    cur_r = R.evaluate(0, apply(base_text, cur, table), cur)
    print("START", cur, cur_r.get("ratio"), cur_r.get("slots"), cur_r.get("bytes"), flush=True)
    pool = [x for x in (a.only.split(",") if a.only else table) if x and x not in cur]
    for rnd in range(a.rounds):
        cands = []
        for mid in pool:
            t = apply(base_text, cur + [mid], table)
            if t is not None:
                cands.append((mid, t))
        print(f"ROUND {rnd}: {len(cands)} candidates", flush=True)
        wq = queue.Queue()
        for w in range(a.workers): wq.put(w)
        def job(t, muts):
            w = wq.get()
            try: return R.evaluate(w, t, muts)
            finally: wq.put(w)
        results = []
        with cf.ThreadPoolExecutor(a.workers) as ex:
            futs = {ex.submit(job, t, cur + [mid]): mid for mid, t in cands}
            for f in cf.as_completed(futs):
                mid = futs[f]; r = f.result(); results.append((mid, r))
                same = r.get("so_sha") == cur_r.get("so_sha")
                print(f"  r{rnd} {mid:34s} {r['status']:14s} bytes={r.get('bytes')} slots={r.get('slots')} ratio={r.get('ratio')} "
                      f"loss={len(r.get('losses',[]))}/{len(r.get('raw_losses',[]))} {'SAME' if same else ''}", flush=True)
        good = [(key(r), mid, r) for mid, r in results if ok(r) and r["ratio"] >= cur_r["ratio"] - a.tol and r.get("so_sha") != cur_r.get("so_sha")]
        good.sort(key=lambda x: x[0])
        if not good or good[0][0] >= key(cur_r):
            print("NO IMPROVEMENT; stop", flush=True); break
        cur.append(good[0][1]); prev_r, cur_r = cur_r, good[0][2]
        if a.prune:
            pool = [mid for _, mid, r in good if mid not in cur]
        else:
            pool = [mid for mid, r in results if r["status"] == "built" and mid not in cur and r.get("so_sha") != prev_r.get("so_sha")]
        print("ACCEPT", cur, cur_r["ratio"], cur_r["slots"], cur_r["bytes"], flush=True)
    print("FINAL", ",".join(cur), cur_r.get("ratio"), cur_r.get("slots"), cur_r.get("bytes"), flush=True)


if __name__ == "__main__":
    main()
