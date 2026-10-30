#!/usr/bin/env python3
"""queue.py <specfile> [workers=2]: each line `name base [knob ...]`; skips names with an existing res file.
Appends one JSON line per finished trial to $OUT/res/log.jsonl."""
import json, os, subprocess, sys, threading, queue as Q
OUT = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w12a13-cto-sizeknobs')
TRIAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trial.py')
spec = [l.split() for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]
nw = int(sys.argv[2]) if len(sys.argv) > 2 else 2
q = Q.Queue()
for s in spec:
    if not os.path.exists(f'{OUT}/res/{s[0]}.json'):
        q.put(s)
lock = threading.Lock()


def worker(i):
    while True:
        try:
            s = q.get_nowait()
        except Q.Empty:
            return
        try:
            fd = os.open(f'{OUT}/res/{s[0]}.claim', os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
        except FileExistsError:
            continue
        if os.path.exists(f'{OUT}/res/{s[0]}.json'):
            continue
        r = subprocess.run(['python3', TRIAL, s[0], s[1], str(i)] + s[2:], text=True, capture_output=True)
        line = (r.stdout.strip().splitlines() or [json.dumps({'name': s[0], 'ok': False, 'error': r.stderr[-500:]})])[-1]
        with lock:
            open(f'{OUT}/res/log.jsonl', 'a').write(line + '\n')


wids = [int(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 else list(range(nw))
ts = [threading.Thread(target=worker, args=(i,)) for i in wids]
for t in ts:
    t.start()
for t in ts:
    t.join()
print('queue done', sys.argv[1])
