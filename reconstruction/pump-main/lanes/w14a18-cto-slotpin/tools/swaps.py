#!/usr/bin/env python3
"""swaps.py <pdir> : colour-level pairwise swaps of 8-byte spill colours on the real frame; dM per swap -> swaps.txt"""
import sys,os,json,subprocess,itertools
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); d=sys.argv[1]
ob=json.load(open(d+'/objs.json')); sp=sorted(k for k,v in ob.items() if v['type']=='spill-slot')
def M(m,tag):
    f=f'{d}/_s{tag}.json'; json.dump(m,open(f,'w'))
    s=subprocess.run(['python3',T+'/slotpin.py','run',d,f,f'{d}/_s{tag}.txt'],capture_output=True,text=True).stdout.split()
    os.remove(f); os.path.exists(f'{d}/_s{tag}.txt') and os.remove(f'{d}/_s{tag}.txt')
    try: return round(float(s[1])*(3339+int(s[4]))/2)
    except Exception: return -1
base=M({},'b')
def ev(p):
    a,b=p; return M({a:ob[b]['off'],b:ob[a]['off']},f'{a}_{b}')-base,a,b
with ThreadPoolExecutor(4) as ex: R=sorted(ex.map(ev,itertools.combinations(sp,2)),reverse=True)
with open(d+'/swaps.txt','w') as f:
    f.write(f'base {base}\n')
    for g,a,b in R: f.write(f'{g} {a} {b} {hex(-ob[a]["off"])} {hex(-ob[b]["off"])}\n')
print('base',base,'top',R[:10])
