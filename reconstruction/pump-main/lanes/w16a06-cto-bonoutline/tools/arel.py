#!/usr/bin/env python3
"""arel.py <m.s> <order(comma asm block names)> [rev=1]: fixed-RA relayout of the span given in explicit asm block names
(blocks of the span not listed follow in their relative order). Prints sc score + errseq."""
import sys,os,json; T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import sub, relayn, sc, eseq
R=relayn.R
def run(p,order,rev=1,out=None):
    pre,blocks,post=R.parse(p); eb=R.explicit(blocks); names=[x[0] for x in eb]
    listed=order.split(','); idx=[names.index(x) for x in listed]; lo,hi=min(idx),max(idx)
    span=names[lo:hi+1]; rest=[x for x in span if x not in listed]
    new=names[:lo]+listed+rest+names[hi+1:]
    t,fl=sub.emit(p,new,rev); o=out or os.path.dirname(p)+'/arel.s'; s=sub.score(t,o)
    r={k:s[k] for k in ('bytes','M','jM','fM','skM')}; r['flips']=fl; r['eseq']=' '.join(map(str,eseq.seq(sc.fn(o))[:10])); return r
if __name__=='__main__':
    print(json.dumps(run(sys.argv[1],sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 1)))
