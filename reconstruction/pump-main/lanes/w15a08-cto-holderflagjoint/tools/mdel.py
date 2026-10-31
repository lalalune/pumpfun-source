#!/usr/bin/env python3
"""mdel.py <in.mir> <out.mir> <blockname-substr,...> <regex> : delete lines matching regex inside the named blocks"""
import sys,re
t=open(sys.argv[1]).read().split('\n'); B=sys.argv[3].split(','); rx=re.compile(sys.argv[4]); cur=''; out=[]; n=0
for l in t:
    m=re.match(r'^  bb\.(\d+)\.?([^:]*):',l)
    if m: cur=m.group(0).strip()
    if any(cur.startswith(b+'.') or cur==b+':' or cur.startswith(b+':') for b in B) and rx.search(l): n+=1; continue
    out.append(l)
open(sys.argv[2],'w').write('\n'.join(out)); print('deleted',n,file=sys.stderr)
