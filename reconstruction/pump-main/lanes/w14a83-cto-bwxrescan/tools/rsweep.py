#!/usr/bin/env python3
"""rsweep.py m.ll out.jsonl [BASESPEC]: reachable-weight single sweep (zero/ptr-heuristic brs -> 1:1; no-heuristic brs -> 20:12, 12:20; plus 16:1/1:16 cold) on any post-opt module"""
import sys,os,json,subprocess,re
sys.path.insert(0,os.path.dirname(__file__)); import bwx
from concurrent.futures import ThreadPoolExecutor
m=sys.argv[1]; out=sys.argv[2]; base=sys.argv[3] if len(sys.argv)>3 else ''
OPT=[p for p in __import__('glob').glob(os.path.expanduser('~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/*/bin/opt'))][0]
r=subprocess.run([OPT,'-passes=print<branch-prob>','-disable-output',m],capture_output=True,text=True).stderr
prob={}
for l in r.split('\n'):
    mm=re.match(r'\s*edge (%\S+) -> (%\S+) probability is 0x([0-9a-f]+)',l)
    if mm: prob.setdefault(mm.group(1).lstrip('%').strip('"'),[]).append(int(mm.group(3),16))
mod=open(m).read(); o=bwx.orig_toks(); items=[]
for lab,c,a,b,_ in bwx.brs(mod):
    p=prob.get(lab,[0])[0]
    if p in (0x30000000,0x50000000): ws=['1:1','16:1','1:16']
    elif p==0x40000000: ws=['20:12','12:20','16:1','1:16']
    else: continue
    items+=[f'bw:{lab}:{w}' for w in ws]
f=open(out,'w')
def go(it):
    x=bwx.run(mod,(base+',' if base else '')+it,o); x['item']=it; f.write(json.dumps(x)+'\n'); f.flush(); return x
with ThreadPoolExecutor(5) as ex: res=list(ex.map(go,items))
b0=bwx.run(mod,base,o); print('base',b0)
for x in sorted(res,key=lambda x:-x.get('ratio',0))[:8]: print(x['item'],x.get('ratio'),x.get('bytes'),x.get('jm'),x.get('fm'),x.get('sk'))
