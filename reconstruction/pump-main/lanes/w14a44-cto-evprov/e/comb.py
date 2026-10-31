#!/usr/bin/env python3
"""comb.py name=a+b+c ... : concatenate EDITS of e/a.py e/b.py ... into e/name.py"""
import sys, os, runpy, json
E = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a44-cto-evprov/e')
for arg in sys.argv[1:]:
    n, spec = arg.split('='); ed = []
    for p in spec.split('+'): ed += [list(x) for x in runpy.run_path(f'{E}/{p}.py')['EDITS']]
    open(f'{E}/{n}.py', 'w').write('EDITS=' + json.dumps(ed) + '\n'); print(n, len(ed))
