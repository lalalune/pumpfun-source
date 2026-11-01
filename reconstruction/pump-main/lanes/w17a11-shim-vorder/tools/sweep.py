#!/usr/bin/env python3
"""sweep.py <out.jsonl> <workers> <spec>... : run vx specs in parallel (fx oracle), append json lines."""
import sys,os,json,shutil
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import vx,fx,errseq,dis,pmv
OUT=os.path.dirname(T)
BASE=os.environ.get('VXBASE',OUT+'/cap_m1/slim.ll')
base=open(BASE).read()
def one(a):
    i,spec=a
    name='sw_%d_%d'%(os.getpid(),i)
    try:
        w,_,m=spec.partition('|')
        t=vx.edit(base,w)
        if m: t=pmv.move(t,m)
    except Exception as e:
        return {'spec':spec,'err':'edit:'+str(e)[:200]}
    r=fx.run(t,name)
    d=OUT+'/fx/'+name
    if 'M' in r:
        b=open(d+'/fn.bin','rb').read(); e=errseq.analyze(b); v=[x for x in e if x['frm']<0x2000]
        r['from']=' '.join(str(x['line']) for x in sorted(v,key=lambda x:x['frm']))
        r['name_ord']=' '.join(str(x['line']) for x in sorted(v,key=lambda x:(x['name'] if x['name'] is not None else 1e9)))
        r['lddw']=sum(1 for o,s in dis.d(b) if s.startswith('lddw'))
    r['spec']=spec
    shutil.rmtree(d,ignore_errors=True)
    return r
if __name__=='__main__':
    outp=sys.argv[1]; nw=int(sys.argv[2]); specs=sys.argv[3:]
    if len(specs)==1 and os.path.exists(specs[0]): specs=[l.strip() for l in open(specs[0]) if l.strip()]
    with open(outp,'a') as f, ThreadPoolExecutor(nw) as ex:
        for r in ex.map(one,list(enumerate(specs))):
            f.write(json.dumps(r)+'\n'); f.flush()
