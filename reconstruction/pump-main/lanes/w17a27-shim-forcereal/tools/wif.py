#!/usr/bin/env python3
"""wif.py <m.ll> <ENVSPEC>...: RAPRIO what-ifs (private llc); ENVSPEC like 'WEIGHT=362=*0.8' or 'HINT=745=r8;PRIO=..'
prints M, bytes and force P/N per spec. Experiment only."""
import sys,os,subprocess,json,hashlib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,fscr
OUT=os.path.dirname(T)
from concurrent.futures import ThreadPoolExecutor
m=sys.argv[1]; specs=sys.argv[2:]
ms=fscr.mset(fscr.toks(open(OUT+'/fx/m0/fn.bin','rb').read()))
FS=[fscr.Force(ms,OUT+'/ra/'+f) for f in ('f_1691_r6.bin','f_1679_r7.bin','f_1626_r3.bin')]
def one(spec):
    env=dict(os.environ)
    for kv in spec.split(';'):
        k,v=kv.split('=',1); env['RAPRIO_'+k]=v
    k=hashlib.sha1(spec.encode()).hexdigest()[:10]; o=f'{OUT}/lx/wif_{k}.o'
    r=subprocess.run([fscr.LLC['p'],*fscr.LLCA,m,'-filetype=obj','-o',o],env=env,capture_output=True,text=True)
    if r.returncode: return spec,{'err':r.stderr[-200:]}
    b=oracle.elf_fn(o,oracle.KEEP); os.remove(o); t=fscr.toks(b); cs=fscr.mset(t)
    res={'M':len(cs),'bytes':len(b)}
    for F in FS: p,pn,n,nn,eq=F.score(cs,t); res[F.name[2:]]=f'{p}/{pn}-{n}/{nn}'+('=' if eq else '')
    return spec,res
with ThreadPoolExecutor(6) as ex:
    for spec,res in ex.map(one,specs): print(spec,json.dumps(res),flush=True)
