#!/usr/bin/env python3
"""tab.py res.jsonl BM: group screen rows into a markdown table (identical-to-main folds collapsed)."""
import sys,json,collections
rows=[json.loads(l) for l in open(sys.argv[1])]; BM=int(sys.argv[2])
fold=[];err=[];g=collections.defaultdict(list)
for r in rows:
    if r['name']=='m0': continue
    if 'error' in r: err.append(r['genes']); continue
    if r.get('eq_main'): fold.append(r['genes']); continue
    g[(r['bytes']-27400,r['M']-BM)].append(r['genes'])
print('| dB | dM | genes |'); print('| ---: | ---: | --- |')
print(f"| 0 | 0 | byte-identical to main: {', '.join(fold)} |")
for (db,dm),v in sorted(g.items(),key=lambda x:(-x[0][1],x[0][0])): print(f"| {db:+d} | {dm:+d} | {', '.join(v)} |")
if err: print(f"| | | compile/apply errors: {', '.join(err)} |")
