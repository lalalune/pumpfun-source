#!/usr/bin/env python3
"""seglen.py <a fn.bin> <b fn.bin> [orig]: call segments whose instruction counts differ (index, start offsets, counts)."""
import sys
sys.path.insert(0, __import__('os').path.dirname(__file__))
def segs(b):
    s = [[0, 0]]; i = 0
    while i < len(b):
        s[-1][1] += 1; n = 16 if b[i] == 0x18 else 8
        if b[i] == 0x85: s.append([i + 8, 0])
        i += n
    return s
A = segs(open(sys.argv[1], 'rb').read()); B = segs(open(sys.argv[2], 'rb').read())
for k, (x, y) in enumerate(zip(A, B)):
    if x[1] != y[1]: print('seg %3d a@%04x b@%04x  n %d -> %d' % (k, x[0], y[0], x[1], y[1]))
