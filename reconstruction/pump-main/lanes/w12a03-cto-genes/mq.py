#!/usr/bin/env python3
"""Batch queue for multi.py screens: two workers, one lane work dir each, until $OUT/MQSTOP exists.

$OUT/mqueue.txt lines: `<tag> <trial> <trial> ...` (trial = name=gene+gene). A tag already present in
multi.jsonl or in $OUT/mq.done is skipped. Lines can be appended while the daemon runs.
"""
import json, os, subprocess, sys, threading, time
from pathlib import Path

OUT = Path.home() / '.cache/pumpfun-reconstruction/lanes/w12a03-cto-genes'
HERE = Path(__file__).resolve().parent
Q = OUT / 'mqueue.txt'
DONE = OUT / 'mq.done'
lock = threading.Lock()
taken = set()


def done_tags():
    t = set()
    if DONE.exists():
        t |= set(DONE.read_text().split())
    return t


def next_batch():
    if not Q.exists():
        return None
    d = done_tags()
    for l in Q.read_text().splitlines():
        p = l.split()
        if not p or p[0].startswith('#') or p[0] in d or p[0] in taken:
            continue
        return p[0], p[1:]
    return None


def worker(w):
    while not (OUT / 'MQSTOP').exists():
        with lock:
            b = next_batch()
            if b:
                taken.add(b[0])
        if not b:
            time.sleep(10)
            continue
        tag, trials = b
        env = dict(os.environ, MULTI_BASE_TAG=os.environ.get('MULTI_BASE_TAG', 'nm2749'), MULTI_BASE_RATIO=os.environ.get('MULTI_BASE_RATIO', '0.45147'))
        with open(OUT / f'{tag}.log', 'w') as fh:
            subprocess.run(['python3', str(HERE / 'multi.py'), tag, str(w)] + trials, stdout=fh, stderr=subprocess.STDOUT, env=env)
        with lock:
            with DONE.open('a') as fh:
                fh.write(tag + '\n')
        print(json.dumps({'batch': tag, 'done': time.strftime('%H:%M:%S')}), flush=True)


if __name__ == '__main__':
    ths = [threading.Thread(target=worker, args=(i,)) for i in range(int(os.environ.get('MQ_PAR', '2')))]
    for t in ths:
        t.start()
    for t in ths:
        t.join()
