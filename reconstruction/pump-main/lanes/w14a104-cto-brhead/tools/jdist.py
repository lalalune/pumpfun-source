import sys,os,difflib
T='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a104-cto-brhead/tools'; sys.path.insert(0,T); import sc,oracle
p=sys.argv[1]; lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
c=sc.fn(p); ct=oracle.mask(c); cj=sc.jmask(ct)
OT=sc.OT; OJ=sc.OJ
sm=difflib.SequenceMatcher(None,OJ,cj,autojunk=False)
coff=[];a=0
for x in ct: coff.append(a); a+=len(x)
for b in sm.get_matching_blocks():
    for k in range(b.size):
        i=b.a+k; j=b.b+k; o=sc.offs[i]
        if lo<=o<hi and OT[i]!=ct[j]:
            oo=int.from_bytes(OT[i][2:4],'little',signed=True); co=int.from_bytes(ct[j][2:4],'little',signed=True)
            print(f'orig {o:#06x} -> tgt {o+8+oo*8:#06x} (off {oo:+d})   cand {coff[j]:#06x} -> {coff[j]+8+co*8:#06x} (off {co:+d})  d={co-oo:+d}')
