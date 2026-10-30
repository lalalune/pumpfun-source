#!/usr/bin/env python3
"""Hill-climb driver: build spelling mutations of v3_buy_costs and measure 0x80df8.

  hc.py eval KEY [KEY ...]          evaluate configurations (2 parallel builds)
  hc.py neigh KEY                   evaluate every one-dimension neighbour of KEY
  hc.py climb KEY [--rounds N]      greedy first-improvement climb with neighbour batches
  hc.py show                        print results sorted by fitness

Results: $OUT/hc/results.jsonl (one row per configuration; cached).
"""
import hashlib, json, os, shutil, subprocess, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parents[4]
HARN = WT / 'reconstruction/harness'
sys.path.insert(0, str(HARN))
sys.path.insert(0, str(HERE))
import mutgen  # noqa: E402

OUT = Path.home() / '.cache/pumpfun-reconstruction/lanes/w7r1-v3buycosts-hillclimb'
HC = OUT / 'hc'
RES = HC / 'results.jsonl'
WORKERS = int(os.environ.get('HC_WORKERS', '2'))
LOCK = threading.Lock()
os.environ['PUMP_BUILD_SLOTS'] = '10'


def load():
    out = {}
    if RES.exists():
        for line in RES.read_text().splitlines():
            r = json.loads(line)
            out[r['key']] = r
    return out


def fitness(r):
    if r.get('status') != 'ok':
        return (-9, 0, 0, 0)
    if r['normalized_equal']:
        return (3, 0, 0, 0)
    return (1, r['ratio'], r['cand_bytes'] == 2120, -(r.get('slots_diff') or 999))


def measure(so):
    from target_metric import measure_window
    from score import original_windows
    from win import Cand
    import re
    w = [w for w in original_windows() if w['start'] == 0x80df8][0]
    cand = Cand(so)
    row = measure_window(w, cand, re.compile('v3_buy_costs'), 1, 12)[0]
    s, n = int(row['cand_start'], 16), row['cand_bytes']
    row['fn_sha'] = hashlib.sha256(cand.fn(s, n)).hexdigest()[:16]
    return row


def slot_src(worker):
    d = OUT / f'src{worker}'
    if not d.exists():
        shutil.copytree(WT / 'programs/pump', d, symlinks=True)
    return d


def apply(src, cfg):
    p = src / 'src/trade_v3.rs'
    orig = (WT / 'programs/pump/src/trade_v3.rs').read_text().split('\n')
    assert orig[364].startswith('fn v3_buy_costs('), orig[364][:40]
    assert orig[376] == '}'
    new = orig[:364] + mutgen.render(cfg) + orig[377:]
    assert len(new) == len(orig)
    p.write_text('\n'.join(new))


def evaluate(key, worker):
    cfg = mutgen.parse(key)
    src = slot_src(worker)
    apply(src, cfg)
    o = HC / 'out' / key
    if o.exists():
        shutil.rmtree(o)
    cmd = [sys.executable, str(HARN / 'fastbuild.py'), '--src', str(src), '--work', str(OUT / f'work{worker}'), '--out', str(o)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    row = {'key': key}
    so = o / 'unstripped.so'
    if not so.exists():
        row['status'] = 'compile-failed'
        tail = (p.stderr or '')[-3000:] + (p.stdout or '')[-1500:]
        errs = [l for l in tail.splitlines() if 'error' in l][:4]
        row['err'] = ' | '.join(errs)[:600]
    else:
        row.update(measure(so))
        row['status'] = 'ok'
        row['unstripped_sha256'] = hashlib.sha256(so.read_bytes()).hexdigest()
    with LOCK:
        with RES.open('a') as f:
            f.write(json.dumps(row) + '\n')
    print(json.dumps({k: row.get(k) for k in ('key', 'status', 'cand_bytes', 'ratio', 'slots_diff', 'calls_candidate', 'fn_sha', 'err')}), flush=True)
    return row


def run(keys):
    HC.mkdir(parents=True, exist_ok=True)
    done = load()
    todo = [k for k in dict.fromkeys(keys) if k not in done]
    queue = list(todo)
    qlock = threading.Lock()

    def worker(w):
        while True:
            with qlock:
                if not queue:
                    return
                k = queue.pop(0)
            try:
                evaluate(k, w)
            except Exception as e:  # keep the batch going
                print(json.dumps({'key': k, 'status': 'driver-error', 'err': repr(e)}), flush=True)

    with ThreadPoolExecutor(WORKERS) as ex:
        list(ex.map(worker, range(WORKERS)))
    return load()


def show(n=40):
    rs = sorted(load().values(), key=fitness, reverse=True)
    for r in rs[:n]:
        print(r['key'], r.get('status'), r.get('cand_bytes'), r.get('ratio'), r.get('slots_diff'), r.get('calls_candidate'), r.get('fn_sha'))
    print(len(rs), 'configs')


def main():
    cmd = sys.argv[1]
    if cmd == 'eval':
        run(sys.argv[2:])
    elif cmd == 'neigh':
        base = mutgen.parse(sys.argv[2])
        run([sys.argv[2]] + [mutgen.key(c) for c in mutgen.neighbors(base)])
        show()
    elif cmd == 'climb':
        cur = sys.argv[2]
        rounds = int(sys.argv[sys.argv.index('--rounds') + 1]) if '--rounds' in sys.argv else 5
        for _ in range(rounds):
            res = run([cur] + [mutgen.key(c) for c in mutgen.neighbors(mutgen.parse(cur))])
            best = max((r for r in res.values()), key=fitness)
            if fitness(best) <= fitness(res[cur]):
                print('local optimum', cur)
                break
            cur = best['key']
            print('move ->', cur, fitness(best))
        show()
    elif cmd == 'show':
        show(int(sys.argv[2]) if len(sys.argv) > 2 else 40)


if __name__ == '__main__':
    main()
