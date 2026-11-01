#!/usr/bin/env python3
"""screen2.py <base.s.ll> <edits.jsonl> <out.jsonl> [workers] [idfilter-regex] [--combo file]: score single edits
(or combos) with fx; also reports W2 exact-LCS delta and do_coin colour (orig 0x5c30 'mov r8,0' present)."""
import sys,os,json,re,shutil
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import fx, rc
from screen import apply
O=rc.orig_window(); OT,OO=rc.mask(O)
REF=os.path.join(fx.OUT,'fx/m0/fn.bin')
R0=rc.per(REF,OT,OO,'')
def wscore(binp):
    d,t,ra,M,b=rc.per(binp,OT,OO,'')
    reg=' '.join(f'{n}:{d.get(n,0)-R0[0].get(n,0):+d}' for _,n in rc.REG if d.get(n,0)!=R0[0].get(n,0))
    C=open(binp,'rb').read()
    # do_coin colour: count 'mov64 r8, imm' (b7 08) in candidate W2-ish range
    n8=sum(1 for i in range(0,len(C)-7,8) if C[i]==0xb7 and C[i+1]==0x08)
    return {'lcs':t,'dlcs':t-R0[1],'W2':d.get('W2',0)-R0[0].get('W2',0),'reg':reg,'movr8':n8}
def main():
    a=sys.argv[1:]; base,ef,outf=a[0],a[1],a[2]; W=int(a[3]) if len(a)>3 else 3
    flt=re.compile(a[4]) if len(a)>4 and a[4]!='-' else None
    L=open(base).read().split('\n')
    E={}
    for l in open(ef):
        e=json.loads(l); E[e['id']]=e
    done=set()
    if os.path.exists(outf):
        for l in open(outf):
            try: done.add(json.loads(l)['id'])
            except Exception: pass
    if '--combo' in a:
        jobs=[l.split() for l in open(a[a.index('--combo')+1]) if l.split() and '+'.join(l.split()) not in done]
    else:
        jobs=[[i] for i in E if i not in done and (flt is None or flt.search(i))]
    print(len(jobs),'jobs',flush=True)
    def run(ids):
        t=apply(L,[E[i] for i in ids])
        if t is None: r={'id':'+'.join(ids),'err':'conflict'}
        else:
            nm='s'+str(abs(hash('+'.join(ids)))%10**9)
            r=fx.run(t,nm); r['id']='+'.join(ids); r.pop('name',None)
            p=os.path.join(fx.OUT,'fx',nm,'fn.bin')
            C=open(p,'rb').read() if os.path.exists(p) else b''
            r['movr8']=sum(1 for i in range(0,len(C)-7,8) if C[i]==0xb7 and C[i+1]==0x08)
            if os.path.exists(p) and (r.get('M',0)>=R0[3]-2 or r['movr8']>0):
                try: r.update(wscore(p))
                except Exception as e: r['werr']=str(e)[:100]
            shutil.rmtree(os.path.join(fx.OUT,'fx',nm),ignore_errors=True)
        with open(outf,'a') as f: f.write(json.dumps(r)+'\n')
        return r
    with ThreadPoolExecutor(W) as ex: list(ex.map(run,jobs))
if __name__=='__main__': main()
