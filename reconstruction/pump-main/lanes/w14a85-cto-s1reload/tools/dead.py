#!/usr/bin/env python3
"""dead.py fn.bin...: CFG-liveness dead stack reloads and same-slot reload/re-spill pairs (split artifacts)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from artifacts import dead_reloads, group
for f in sys.argv[1:]:
    g = group(dead_reloads(open(f, 'rb').read()))
    print('#', f, len(g), 'sites')
    for s in g:
        print('%04x %-5s r%d %s%s' % (s['off'], s['kind'], s['reg'], ' '.join('-0x%x' % -x for x in s['slots']),
                                     ('  rc@%04x' % s['rc']) if s['rc'] is not None else ''))
