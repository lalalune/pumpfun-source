#!/usr/bin/env python3
"""perobj.py <pdir> <map.json> : pin each moved object alone (and leave-one-out from the full map); dM per object"""
import sys,os,json,subprocess
T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T)
d,mpf=sys.argv[1:3]; mp=json.load(open(mpf)); ob=json.load(open(d+'/objs.json'))
def M(m):
    json.dump(m,open(d+'/_t.json','w'))
    s=subprocess.run(['python3',T+'/slotpin.py','run',d,d+'/_t.json',d+'/_t.txt'],capture_output=True,text=True).stdout.split()
    r=float(s[1]); n=int(s[4]); return round(r*(3339+n)/2)
base=M({}); full=M(mp); rows=[]
for k,t in mp.items():
    if t==ob[k]['off']: continue
    a=M({k:t}); l=M({kk:v for kk,v in mp.items() if kk!=k})
    rows.append((a-base,full-l,k,ob[k]['off'],t,ob[k]['size'],ob[k]['type'],ob[k]['name']))
print('base',base,'full',full)
for r in sorted(rows,reverse=True): print(*r)
