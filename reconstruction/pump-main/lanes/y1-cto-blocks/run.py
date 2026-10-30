#!/usr/bin/env python3
"""Exhaustive local permutation driver for admin_cto::execute (0x22a10).

  run.py --base g1,g2 --genes g3,g4,...   build base+each gene (2 workers, 1 cargo job each),
                                          score target_metric and score.py, record in the ledger.
  run.py --base g1,g2 --combo             build exactly base (one variant) and record it.
Results append to <cache>/results.jsonl.
"""
import argparse, json, subprocess, shutil, sys, threading, queue, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import genes as GN

LANE = 'y1-cto-blocks'; BASESHA = 'dce6faf97'; TARGET = '0x22a10'
WT = Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/y1-cto-blocks')
REPO = WT  # harness from the worktree (same as main)
CACHE = Path.home() / '.cache/pumpfun-reconstruction/lanes' / LANE
BASELINE = '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/y-baseline/0bcf7223c/score.json'
SRC = WT / 'programs/pump'
REL = 'src/creator/admin_cto.rs'
BASEFILE = CACHE / 'admin_cto.base.rs'  # frozen copy of main dce6faf97's file
LOG = REPO / 'reconstruction/pump-main/log_attempt.py'
BASE_RATIO, BASE_SIZE = 0.37637, 27344
lock = threading.Lock()

def apply(names):
    s = BASEFILE.read_text(); n0 = s.count('\n')
    for g in names:
        for o, n in GN.G[g]:
            if s.count(o) != 1: raise ValueError(f'{g}: {o[:40]!r} count {s.count(o)}')
            s = s.replace(o, n)
    assert s.count('\n') == n0
    return s

def key(mech): return f'{TARGET}-{BASESHA}-blocks-{mech}-v1'

def ledger(mech, hyp, status, data):
    subprocess.run([sys.executable, str(LOG), 'record', '--lane', LANE, '--approach', 'blocks', '--target', TARGET,
                    '--dedupe-key', key(mech), '--hypothesis', hyp, '--status', status, '--data', json.dumps(data)],
                   cwd=REPO, check=False, capture_output=True)

def dup(mech):
    r = subprocess.run([sys.executable, str(LOG), 'check', '--dedupe-key', key(mech)], cwd=REPO, capture_output=True, text=True)
    return json.loads(r.stdout)['duplicate']

def build(worker, names, mech):
    src = CACHE / f'src_w{worker}'
    if not src.exists(): shutil.copytree(SRC, src, symlinks=True)
    (src / REL).write_text(apply(names))
    work = CACHE / f'work_w{worker}'; out = CACHE / f'out_w{worker}'
    r = subprocess.run(['nice', '-n', '10', 'env', 'CARGO_BUILD_JOBS=1', sys.executable, str(REPO / 'reconstruction/harness/fastbuild.py'),
                        '--src', str(src), '--work', str(work), '--out', str(out)], capture_output=True, text=True, cwd=REPO)
    so = out / 'unstripped.so'
    if r.returncode != 0 or not so.exists() or '"ok": false' in r.stdout:
        return {'mech': mech, 'genes': names, 'status': 'compile-failed', 'tail': (r.stdout + r.stderr)[-800:]}
    tm = subprocess.run([sys.executable, str(REPO / 'reconstruction/harness/target_metric.py'), str(so), TARGET, '--sym', r'admin_cto::execute$', '--top', '1'],
                        capture_output=True, text=True, cwd=REPO).stdout.strip().splitlines()
    m = json.loads(tm[0]) if tm else {}
    sj = out / 'score.json'
    subprocess.run([sys.executable, str(REPO / 'reconstruction/harness/score.py'), str(so), '--baseline', BASELINE, '--json', str(sj)], capture_output=True, cwd=REPO)
    sm = json.loads(sj.read_text())['summary']
    cand_sha = hashlib.sha256(so.read_bytes()).hexdigest()[:12]
    shutil.copy(so, CACHE / f'so_{mech}.so')
    return {'mech': mech, 'genes': names, 'ratio': m.get('ratio'), 'size': m.get('cand_bytes'), 'calls': m.get('calls_candidate'),
            'normalized': sm['normalized'], 'raw': sm['raw'], 'losses': len(sm['losses']), 'raw_losses': len(sm['raw_losses']),
            'gains': len(sm['gains']), 'raw_gains': len(sm['raw_gains']), 'sha': cand_sha}

def run(jobs, base_ratio):
    q = queue.Queue()
    for j in jobs: q.put(j)
    def worker(w):
        while True:
            try: names, mech, hyp = q.get_nowait()
            except queue.Empty: return
            if dup(mech):
                print('skip duplicate', mech, flush=True); continue
            res = build(w, names, mech)
            if res.get('status') == 'compile-failed':
                st = 'compile-failed'
            else:
                clean = res['losses'] == 0 and res['raw_losses'] == 0
                better = clean and ((res['ratio'] is not None and res['ratio'] > base_ratio + 1e-6 and res['calls'] == [154, 3]) or res['gains'] > 0 or res['raw_gains'] > 0)
                st = 'partial' if better else 'rejected'
            res['status'] = st; res['base_ratio'] = base_ratio
            note = f"ratio {res.get('ratio')} size {res.get('size')} (base {base_ratio}); losses {res.get('losses')}/{res.get('raw_losses')}; calls {res.get('calls')}; sha {res.get('sha')}"
            ledger(mech, hyp, st, {'note': note, **{k: v for k, v in res.items() if k != 'tail'}})
            with lock:
                with open(CACHE / 'results.jsonl', 'a') as f: f.write(json.dumps(res) + '\n')
                print(json.dumps(res), flush=True)
    ts = [threading.Thread(target=worker, args=(w,)) for w in range(2)]
    for t in ts: t.start()
    for t in ts: t.join()

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default=''); ap.add_argument('--genes', default=''); ap.add_argument('--base-ratio', type=float, default=BASE_RATIO)
    ap.add_argument('--combo', action='store_true'); ap.add_argument('--tag', default='')
    a = ap.parse_args()
    base = [g for g in a.base.split(',') if g]
    if a.combo:
        mech = 'combo-' + '+'.join(base)
        jobs = [(base, mech, f'permutation combo on main {BASESHA}: ' + ', '.join(base))]
    else:
        gs = [g for g in a.genes.split(',') if g] or [g for g in GN.G if g not in base]
        pre = ('on-' + a.tag + '-') if a.tag else ''
        jobs = [(base + [g], pre + g, f'local permutation {g} on main {BASESHA}' + (f' + [{",".join(base)}]' if base else '') + ': ' + GN.G[g][0][1][:120]) for g in gs]
    run(jobs, a.base_ratio)
