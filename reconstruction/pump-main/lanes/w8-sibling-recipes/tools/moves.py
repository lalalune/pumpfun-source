"""Evaluate source-level moves in the fast model.
moves.py <cand.so> <refined.json> <spec.json>
spec: list of [ [regex,...] units to move (kept in our relative order), "after"|"before", anchor_regex ]
Prints raw count, gains, losses relative to the as-built order."""
import sys,json,re
sys.path.insert(0,__file__.rsplit('/',1)[0])
import fastmodel as F
def apply(M,order,spec):
    for item in spec:
        pats,kind,anc=item[:3]
        mv=[a for a in order if any(re.search(p,M.names[a]) for p in pats)]
        if len(item)>3 and item[3]=='orig': mv.sort(key=lambda a:M.inv.get(a,1<<40))
        if not mv: raise SystemExit(f'no units for {pats}')
        rest=[a for a in order if a not in mv]
        ancs=[a for a in rest if re.search(anc,M.names[a])]
        if not ancs: raise SystemExit(f'no anchor {anc}')
        i=rest.index(ancs[-1])+1 if kind=='after' else rest.index(ancs[0])
        order=rest[:i]+mv+rest[i:]
    return order
def p16(M,order):
    fix=lambda a: M.wins[M.inv[a]]['bytes'] if M.inv[a] in M.UN else M.units[a][0]
    o=[a for a in order if a in M.inv]
    return len(M.eval(o,fix,data_ok=True))
def order_stats(M,order):
    import bisect
    seq=[M.inv[a] for a in order if a in M.inv]
    t=[]
    for x in seq:
        i=bisect.bisect_left(t,x)
        if i==len(t): t.append(x)
        else: t[i]=x
    L=[M.inv[a] for a in order if a in M.inv and M.region(a)=='L']
    ost=sorted(L); nxt={ost[i]:ost[i+1] for i in range(len(ost)-1)}
    br=sum(1 for i in range(len(L)-1) if nxt.get(L[i])!=L[i+1])
    return (len(t),br)
if __name__=='__main__':
    M=F.Model(sys.argv[1],sys.argv[2]); spec=json.load(open(sys.argv[3]))
    base=M.eval(M.cst); r=M.eval(apply(M,list(M.cst),spec))
    print('raw',len(base),'->',len(r),'gains',sorted(hex(x) for x in r-base),'losses',sorted(hex(x) for x in base-r))
    print('P16 (16 matched, extras gone, data equal)',p16(M,M.cst),'->',p16(M,apply(M,list(M.cst),spec)))
    print('LIS/L-breaks',order_stats(M,M.cst),'->',order_stats(M,apply(M,list(M.cst),spec)))
