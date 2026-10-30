#!/usr/bin/env python3
"""irdiff.py <a fn.ll> <b fn.ll> [n]: unified diff of two execute IR bodies with value names, labels and metadata masked."""
import re, sys, difflib
def norm(p):
    out = []
    for l in open(p):
        l = l.rstrip()
        if re.match(r'^\S.*:\s*(;.*)?$', l): l = 'L:'
        l = re.sub(r'%[\w.$"-]+|%"[^"]*"', '%v', l); l = re.sub(r'!\d+', '!m', l); l = re.sub(r'#\d+', '#a', l)
        out.append(l[:170])
    return out
a, b = norm(sys.argv[1]), norm(sys.argv[2]); n = int(sys.argv[3]) if len(sys.argv) > 3 else 200
for l in list(difflib.unified_diff(a, b, n=1, lineterm=''))[:n]: print(l)
