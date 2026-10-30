#!/usr/bin/env python3
"""attrib.py <sdir>: alloca-level attribution. For each IR alloca, move it alone to a free far offset and record which output
lines change -> line -> alloca id. Writes <sdir>/attr.json {line_index: alloca_id}"""
import sys,os,json,subprocess
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); d=sys.argv[1]
ob=json.load(open(d+'/objs.json')); col=json.load(open(d+'/col.json'))
real=[l.split(None,1)[1].strip() for l in open(d+'/real.txt')]
sys.path.insert(0,T); import slotpin as S; RO=S._offs(real)
def one(k):
    o=ob[k]; m=dict(col); m[k]=-0xd00-((o['size']+7)//8*8)
    mf=f'{d}/_a{k}.json'; json.dump(m,open(mf,'w'))
    subprocess.run(['python3',T+'/slotpin.py','run',d,mf,f'{d}/_a{k}.txt'],capture_output=True)
    try: L=[l.split(None,1)[1].strip() for l in open(f'{d}/_a{k}.txt')]
    except Exception: return k,None
    os.remove(mf); os.remove(f'{d}/_a{k}.txt')
    if len(L)!=len(real): return k,'len'
    return k,[i for i,(a,b) in enumerate(zip(real,L)) if a!=b and RO[i] is not None and RO[i]>-0x8d0]
A={}; bad=[]
with ThreadPoolExecutor(4) as ex:
    for k,r in ex.map(one,list(ob)):
        if not isinstance(r,list): bad.append((k,r)); continue
        for i in r:
            if i in A: bad.append((k,'dup',i))
            A[i]=int(k)
json.dump(A,open(d+'/attr.json','w')); print('attributed lines',len(A),'issues',bad[:10],len(bad))
