#!/usr/bin/env python3
"""show.py [prefix ...]: print res/cap.jsonl rows (optionally only names with one of the prefixes)."""
import sys,json,os
OUT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pre=tuple(sys.argv[1:])
for l in open(OUT+'/res/cap.jsonl'):
    r=json.loads(l)
    if pre and not r['name'].startswith(pre): continue
    if 'err' in r: print('%-26s ERR %s'%(r['name'],str(r.get('detail'))[:140]))
    else: print('%-26s M=%d B=%d dM=%+d slots=%s sig=%s  %s'%(r['name'],r['M'],r['bytes'],r['M']-r.get('mainM',2295),r.get('slots'),r['sig'],','.join(r['genes'])[:90]))
