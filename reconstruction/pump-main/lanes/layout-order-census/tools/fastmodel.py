"""Fast raw-layout model for move searches. Import: M=Model(cand_so, refined_json)."""
import sys,json,bisect,re
sys.path.insert(0,__file__.rsplit('/',1)[0])
import census as C
from pathlib import Path
class Model:
    def __init__(s,cpath,refp):
        cpath=Path(cpath); ref=json.load(open(refp))
        orig=(C.BASE/'original.so').read_bytes(); osec=C.sections(orig)
        cand=cpath.read_bytes(); csec=C.sections(cand)
        s.osec,s.csec=osec,csec
        wins={w['start']:w for w in C.original_windows()}; ost=sorted(wins)
        pair={int(k,16):int(v,16) for k,v in ref['pair'].items()}; inv={v:k for k,v in pair.items()}
        units={}
        for a,sz,n in C.candidate_functions(cpath): units.setdefault(a,[sz,n])
        cst=sorted(units); s.units,s.cst,s.pair,s.inv,s.wins,s.ost=units,cst,pair,inv,wins,ost
        s.names={a:units[a][1] for a in cst}
        cfn=lambda x: cst[bisect.bisect_right(cst,x)-1]
        UN=set(C.UNMATCHED_NAMES); s.UN=UN
        s.checks=[]  # per window: (s, a, calls[(off, callee, coff, odelta)], tl[(callee,coff,oabs)], hasdata)
        for st in ost:
            if st in UN: continue
            a=pair[st]; craw=C.body(cand,csec,a,units[a][0])
            oo=C.operands(wins[st]['raw'],st,osec); co=C.operands(craw,a,csec)
            calls=[];tl=[];hd=False
            for x,y in zip(oo,co):
                if x[1]=='call':
                    c=cfn(y[2]); calls.append((x[0],c,y[2]-c,x[2]-(st+x[0]+8)))
                elif x[3]=='.text':
                    c=cfn(y[2]); tl.append((c,y[2]-c,x[2]))
                else: hd=True
            s.checks.append((st,a,calls,tl,hd))
        s.text0=csec['.text']['addr']
        mend=[a for a in cst if s.names[a]=='__rust_alloc_error_handler'][0]
        main=[a for a in cst if a<mend and a in inv]
        s.lstart=next(main[i] for i in range(1,len(main)) if s.names[main[i]]<s.names[main[i-1]])
        s.mend=mend
    def region(s,a): return 'U' if a<s.lstart else ('L' if a<s.mend else 'D')
    def eval(s,order,sizefn=None,data_ok=False):
        sz=sizefn or (lambda a: s.units[a][0])
        na={};p=s.text0
        for a in order: na[a]=p; p+=sz(a)
        tsize=p-s.text0
        dok=data_ok or tsize==s.osec['.text']['size']
        rawset=set()
        for st,a,calls,tl,hd in s.checks:
            if hd and not dok: continue
            base=na[a]; ok=True
            for off,c,coff,od in calls:
                if c not in na or na[c]+coff-(base+off+8)!=od: ok=False;break
            if ok:
                for c,coff,oabs in tl:
                    if c not in na or na[c]+coff!=oabs: ok=False;break
            if ok: rawset.add(st)
        return rawset
