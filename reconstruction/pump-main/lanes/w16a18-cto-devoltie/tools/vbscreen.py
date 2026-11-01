#!/usr/bin/env python3
"""vbscreen.py <out.jsonl> [mode]: splice-screen vol334_back (vb) on main 5998913 against cached captures (experiment only).
mode 'single' (default): vb + each capture X with delta_bytes in DELTAS (env, default 8).
mode 'pairs': vb + X + Y with X.delta+Y.delta == 8 (X,Y with M >= MMIN).
Captures on the 9bd38c7-equivalent source are spliced as splice(main9bd,[main1f,vb9bd,X]); captures on 1f4e396/5998913
(ev6+A6 already in) as splice(main9bd,[vb9bd,X]). Prints bytes, M, slots for each composite."""
import sys,os,json,itertools,multiprocessing as mp
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import splice, oracle
C='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes'
OUT=C+'/w16a18-cto-devoltie'
M9=open(OUT+'/rx/main9bd/fn.bin','rb').read()
M1F=open(C+'/w16a02-cto-faithknobs/rx/main1f/fn.bin','rb').read()
VB=open(C+'/w15a03-cto-stitch15/rx/N_vol334_back/fn.bin','rb').read()
B=splice.parse(M9); BT=splice.targets(B)
OR=oracle.orig_window(); OB=b''.join(oracle.mask(OR))
def slots(raw):
    cb=b''.join(oracle.mask(raw))
    return sum(1 for i in range(0,len(OB),8) if OB[i:i+8]!=cb[i:i+8]) if len(OB)==len(cb) else None
VM1F=splice.Var(B,M1F); VVB=splice.Var(B,VB)
def lib():
    rows=json.load(open(C+'/w16a02-cto-faithknobs/catalog4.json'))
    out=[]
    for r in rows:
        fb=f"{C}/{r['lane']}/rx/{r['name']}/fn.bin"
        if os.path.exists(fb): out.append(dict(name=r['name'],lane=r['lane'],genes=r.get('genes',''),fb=fb,src='9bd',d=r['delta_bytes'],M=r['M']))
    extra=os.environ.get('EXTRA')   # json list of {name,lane,fb,src} on 1f
    if extra:
        for r in json.load(open(extra)): out.append(r)
    return out
L=lib()
def comp(xs):
    vs=[VVB]
    if any(x['src']=='9bd' for x in xs) or True: pass
    # 9bd captures need main1f's diff; 1f captures already carry it (they conflict with VM1F, so leave it out)
    if all(x['src']=='9bd' for x in xs): vs=[VM1F,VVB]
    elif any(x['src']=='9bd' for x in xs):
        vs=[VVB]   # mixed: 1f capture supplies ev6+A6
    raws=[open(x['fb'],'rb').read() for x in xs]
    s=splice.splice(M9,vs+[splice.Var(B,r) for r in raws],B,BT)
    if s is None: return None
    return len(s),splice.M(s),slots(s)
def ev1(i):
    x=L[i]; r=comp([x])
    return (x['name'],x['lane'],x['d'],x['M'],r)
def ev2(ij):
    i,j=ij; r=comp([L[i],L[j]])
    return (L[i]['name']+'+'+L[j]['name'],L[i]['lane']+'+'+L[j]['lane'],L[i]['d']+L[j]['d'],(L[i]['M'],L[j]['M']),r)
if __name__=='__main__':
    outf=sys.argv[1]; mode=sys.argv[2] if len(sys.argv)>2 else 'single'
    if mode=='single':
        D=[int(x) for x in os.environ.get('DELTAS','8').split(',')]
        jobs=[i for i,x in enumerate(L) if x['d'] in D]; fn=ev1
    else:
        MMIN=int(os.environ.get('MMIN','2236')); idx=[i for i,x in enumerate(L) if x['M']>=MMIN and x['d']!=0 and abs(x['d'])<=int(os.environ.get('DMAX','128'))]
        jobs=[(i,j) for i,j in itertools.combinations(idx,2) if L[i]['d']+L[j]['d']==8]; fn=ev2
    print(len(L),'captures,',len(jobs),'jobs',flush=True)
    with mp.get_context('fork').Pool(int(os.environ.get('NP','4'))) as P: res=P.map(fn,jobs,chunksize=4)
    res=[r for r in res if r[4] is not None]
    res.sort(key=lambda r:(-(r[4][1] if r[4][0]==27400 else r[4][1]-99), r[4][2] if r[4][2] is not None else 9999))
    with open(outf,'w') as f:
        for r in res: f.write(json.dumps({'names':r[0],'lanes':r[1],'delta':r[2],'Ms':r[3],'bytes':r[4][0],'M':r[4][1],'slots':r[4][2]})+'\n')
    for r in res[:25]: print(r)
