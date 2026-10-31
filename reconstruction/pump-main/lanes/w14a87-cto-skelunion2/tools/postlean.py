#!/usr/bin/env python3
"""postlean.py <results.jsonl> <out.jsonl>: per capture: base, Br, h7+Br -> bytes and M only (fast)."""
import sys,os,json,subprocess
T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T)
import sc, relayn, oracle
def M(p):
    c=sc.fn(p); ct=oracle.mask(c); return len(c),sum(sc.hits(sc.OT,ct))
done=set()
if os.path.exists(sys.argv[2]):
    for l in open(sys.argv[2]): done.add(json.loads(l)['name'])
for l in open(sys.argv[1]):
    r=json.loads(l); n=r['name']
    if 'ratio' not in r or n in done: continue
    d=f'{O}/rx/{n}'; out={'name':n,'spec':r['spec']}
    try:
        if not os.path.exists(d+'/m.s'): subprocess.run(['bash',T+'/llc.sh',d+'/m.ll',d+'/m.s'],check=True)
        out['b'],out['M']=M(d+'/m.s')
        x=relayn.run_rev(d+'/m.s',d+'/mBr.s','B'); out['Br_b'],out['Br_M'],out['miss']=x['bytes'],x['M'],x['miss']
        h=subprocess.run(['python3',T+'/h7.py',d+'/m.ll',d+'/h7.ll'],capture_output=True,text=True)
        if h.returncode==0:
            subprocess.run(['bash',T+'/llc.sh',d+'/h7.ll',d+'/h7.s'],check=True); os.remove(d+'/h7.ll')
            x=relayn.run_rev(d+'/h7.s',d+'/h7Br.s','B'); out['h7Br_b'],out['h7Br_M']=x['bytes'],x['M']
    except Exception as e: out['err']=repr(e)[:200]
    open(sys.argv[2],'a').write(json.dumps(out)+'\n'); print(json.dumps(out))
