#!/usr/bin/env python3
"""dumps.py build.log OUTDIR : split print-changed dumps of swap_hop into numbered files."""
import sys, re, os
log = open(sys.argv[1], errors='replace').read()
od = sys.argv[2]; os.makedirs(od, exist_ok=True)
parts = re.split(r'\n?\*\*\* IR Dump After (.*?) \*\*\*\n', log)
k = 0
for i in range(1, len(parts), 2):
    name, body = parts[i], parts[i+1]
    if 'swap_hop' not in name: continue
    k += 1
    nm = re.sub(r'[^\w]+', '_', name.split(' on ')[0])[:40]
    # cut body at the end of the function / machine function
    open(f'{od}/{k:03d}_{nm}.txt', 'w').write(body)
print(k)
