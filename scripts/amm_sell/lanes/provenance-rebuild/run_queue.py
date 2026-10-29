#!/usr/bin/env python3
"""Build a queue of sell.rs files through try_sell.py on slots 0/1. Usage: run_queue.py QUEUE.json RESULTS.jsonl APPROACH"""
import json, subprocess, sys, threading, queue
from pathlib import Path

SWARM = Path('/Users/shawwalters/Documents/Codex/2026-10-24/amm-sell-swarm')
qfile, rfile, approach = sys.argv[1], sys.argv[2], sys.argv[3]
items = json.loads(Path(qfile).read_text())  # [{file, hypothesis}]
done = set()
if Path(rfile).exists():
    for l in Path(rfile).read_text().splitlines():
        done.add(json.loads(l)['file'])
q = queue.Queue()
for it in items:
    if it['file'] not in done:
        q.put(it)
lock = threading.Lock()


def worker(slot):
    while True:
        try:
            it = q.get_nowait()
        except queue.Empty:
            return
        p = subprocess.run(['python3', '-B', 'harness/try_sell.py', '--lane', 'provenance-rebuild', '--approach', approach,
                            '--hypothesis', it['hypothesis'][:400], '--sell', it['file'], '--slot', str(slot)],
                           cwd=SWARM, capture_output=True, text=True)
        res = {'file': it['file'], 'rc': p.returncode}
        try:
            e = json.loads(p.stdout)
            m = e.get('metrics') or {}
            res.update(status=e.get('status'), dup=e.get('duplicate'), key=e.get('key', '')[:16],
                       dist=m.get('align_distance'), slots=m.get('slot_diffs'), size=m.get('sell_size'),
                       lost=m.get('lost_windows_normalized_count'),
                       jeq=any('jeq r2, r' in x for x in (m.get('borrow_branch') or [])), out=e.get('out_dir'))
        except Exception:
            res['err'] = (p.stdout[-300:] + p.stderr[-300:])
        with lock:
            with open(rfile, 'a') as f:
                f.write(json.dumps(res) + '\n')
            if res.get('rc') == 3:
                print('GOAL', res, flush=True)


ts = [threading.Thread(target=worker, args=(s,)) for s in (0, 1)]
[t.start() for t in ts]
[t.join() for t in ts]
print('done')
