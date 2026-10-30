#!/usr/bin/env python3
"""qadd.py <pos|top|end> <set> [<set> ...]  insert sets into queue.txt under the daemon's lock.
   qadd.py show   print queue;  qadd.py drop <substring>  remove matching lines"""
import sys, fcntl
from pathlib import Path
Q = Path.home() / '.cache/pumpfun-reconstruction/lanes/w12a14-cto-hillclimb/hc/queue.txt'
with open(str(Q) + '.lock', 'w') as lk:
    fcntl.flock(lk, fcntl.LOCK_EX)
    lines = [l.strip() for l in Q.read_text().splitlines() if l.strip()] if Q.exists() else []
    cmd = sys.argv[1]
    if cmd == 'show':
        for i, l in enumerate(lines): print(i, l)
        sys.exit(0)
    if cmd == 'drop':
        lines = [l for l in lines if sys.argv[2] not in l]
    else:
        new = [s for s in sys.argv[2:] if s not in lines]
        pos = 0 if cmd == 'top' else (len(lines) if cmd == 'end' else int(cmd))
        lines = lines[:pos] + new + lines[pos:]
    Q.write_text('\n'.join(lines) + '\n')
    print(len(lines), 'queued')
