#!/usr/bin/env python3
"""ev.py <obj|fn.bin>... : ratio/slots/bytes/eq_main, fmr plain/L1/L2, clonefeat spill/reg, regmiss in clone run
[0x2800,0x4a78) and sweep-join region [0x4a78,0x5600). Experiment only."""
import sys,os,json,difflib,collections
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
src=open(T+'/rx.py').read(); g={'__name__':'x'}; exec(src.split("OUT=os.environ")[0],g)
import types
C=types.ModuleType('C'); _s=open(T+'/cls.py').read(); C.__dict__['__file__']=T+'/cls.py'; exec(_s[:_s.index('def main')],C.__dict__)
from bdis import decode
import clonefeat
O=g['orig_window']()
bs=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
MM=g['mask'](g['elf_fn'](bs,g['KEEP']))
def toks(raw,l): return [C.mask(t,l) for _,t in C.insns(raw)]
def tokk(raw): return [t for _,t in C.insns(raw)]
OI=decode(O)
def regmiss(c,lo,hi):
    ci=decode(c)
    sm=difflib.SequenceMatcher(None,toks(O,2),toks(c,2),autojunk=False)
    o1=toks(O,1); c1=toks(c,1); tot=0; miss=collections.Counter(); n=0
    for a,b,k in sm.get_matching_blocks():
        for i in range(k):
            od=OI[a+i]; cd=ci[b+i]
            if not (lo<=od['off']<hi): continue
            tot+=1
            if o1[a+i]!=c1[b+i]:
                n+=1
                for f in ('dst','src'):
                    if od[f]!=cd[f]: miss[(od[f],cd[f])]+=1
    return tot,n,miss
def ev(p,label=None):
    c=open(p,'rb').read() if p.endswith('.bin') else g['elf_fn'](p,g['KEEP'])
    r,sd=g['metric'](c,O)
    fm=[]
    for l in (1,2):
        fm.append(round(difflib.SequenceMatcher(None,toks(O,l),toks(c,l),autojunk=False).ratio(),5))
    s,rg=clonefeat.feats(tokk(c))
    t1,n1,m1=regmiss(c,0x2800,0x4a78); t2,n2,m2=regmiss(c,0x4a78,0x5600)
    return {'o':label or p.split('/')[-1],'ratio':round(r,5),'slots':sd,'bytes':len(c),'eq_main':g['mask'](c)==MM,'L1':fm[0],'L2':fm[1],
            'cf':f'{s}/{rg}','clone_L2':t1,'clone_regmiss':n1,'join_L2':t2,'join_regmiss':n2,
            'top':' '.join('r%d>r%d:%d'%(a,b,k) for (a,b),k in m1.most_common(5))}
if __name__=='__main__':
    for p in sys.argv[1:]: print(json.dumps(ev(p)))
