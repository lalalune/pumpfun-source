#!/usr/bin/env python3
"""score.py fn.bin...: rx metric (ratio, slots) + fmr L0/L1/L2 for function binaries."""
import sys, os, subprocess
D = os.path.dirname(os.path.abspath(__file__))
src = open(D + '/rx.py').read(); g = {'__name__': 'x'}; exec(src[:src.index("OUT=os.environ.get")], g)
o = g['orig_window']()
for f in sys.argv[1:]:
    c = open(f, 'rb').read(); r, sd = g['metric'](c, o)
    fm = subprocess.run([sys.executable, D + '/fmr.py', f], capture_output=True, text=True).stdout.strip()
    print(round(r, 5), sd, len(c), '|', fm)
