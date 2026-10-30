#!/usr/bin/env python3
"""perint.py <tag>: interval-level single moves on top of the real colouring: each interval alone to its orig-pin target; dM"""
import sys,os,subprocess,json
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T=O+'/tools'
tag=sys.argv[1]; d=f'{O}/q/{tag}'; col=json.load(open(d+'/col.json')); tgt=json.load(open(d+'/i_orig.json')); ob=json.load(open(d+'/objs.json'))
def M(m):
    json.dump(m,open(d+'/_t.json','w'))
    s=subprocess.run(['python3',T+'/slotpin.py','run',d,d+'/_t.json',d+'/_t.txt'],capture_output=True,text=True).stdout.split()
    return round(float(s[1])*(3339+int(s[4]))/2)
base=M(col); rows=[]
for k,t in tgt.items():
    if col.get(k)==t: continue
    m=dict(col); m[k]=t; rows.append((M(m)-base,k,col.get(k),t,ob[k]['type'],ob[k]['size'],ob[k]['name']))
print('base',base)
for r in sorted(rows,reverse=True)[:40]: print(*r)
