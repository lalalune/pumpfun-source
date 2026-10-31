#!/usr/bin/env python3
"""shperm.py <rxname> <lo_hex> <hi_hex> <d>: fshift the alloca band (-lo,-hi] by d, then spill-colour bestperm (+swap climb).
Bound for 'alloca shift undone + best spill colouring' of the same code."""
import sys,os,struct,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import relab as R
n,lo,hi,d=sys.argv[1],-int(sys.argv[2],16),-int(sys.argv[3],16),int(sys.argv[4])
D=os.path.dirname(T)+'/rx/'+n; b=open(D+'/fn.bin','rb').read(); sp=R.spills(D+'/pei.mir')
c=bytearray(b); lea={}
for i,k in R.ins(b):
    op=b[i]; dst=b[i+1]&15; src=b[i+1]>>4
    if op==0xbf and src==10: lea[dst]=i; continue
    if op==0x07 and dst in lea and lea[dst]==i-8:
        v=struct.unpack_from('<i',b,i+4)[0]
        if lo<v<=hi: struct.pack_into('<i',c,i+4,v+d)
        lea.pop(dst,None); continue
    o=R.memoff(b,i)
    if o is not None and lo<o<=hi and o not in sp: struct.pack_into('<h',c,i+2,o+d)
    lea.pop(dst,None)
c=bytes(c); m0=R.M(b); m1=R.M(c); mp,pm=R.bestperm(c,sp,3)
cur=dict(pm); best=mp
for rnd in range(2):
    bb=R.apply(c,cur); V=R.votes(bb,set(cur.values())); inv={v:k for k,v in cur.items()}; cand=set(); imp=0
    for y,dd in V.items():
        for x in dd:
            if x in inv and x!=y: cand.add(tuple(sorted((y,x))))
    for y,x in sorted(cand):
        a,e=inv[y],inv[x]; t=dict(cur); t[a],t[e]=cur[e],cur[a]; m=R.M(R.apply(c,t))
        if m>best: best=m; cur=t; inv={v:k for k,v in cur.items()}; imp+=1
    if not imp: break
print(json.dumps({'n':n,'bytes':len(b),'M':m0,'Mshift':m1,'Mshperm':mp,'Mshhc':best,'ratio_shhc':R.ratio(R.apply(c,cur)),'ratio_shift':R.ratio(c)}))
