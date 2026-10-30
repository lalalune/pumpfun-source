import sys,os,difflib
T='tools'; sys.path.insert(0,T); import absratio as A, amap
for p in sys.argv[1:]:
    C=amap.lines(p); OL=amap.OL
    a=[A.norm(x[1],True) for x in OL]; b=[A.norm(x[1],True) for x in C]
    sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
    ins=[];dele=[]
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag=='equal': continue
        d=(j2-j1)-(i2-i1)
        ins.append((C[j1][0] if j1<len(C) else 'end',OL[i1][0] if i1<len(OL) else 'end',i2-i1,j2-j1))
    print(p,len(C),len(OL))
    # region-wise net: bucket by orig offset 0x400
    import collections
    net=collections.Counter()
    for c,o,ni,nj in ins: net[int(o,16)//0x400 if o!='end' else 99]+=nj-ni
    print(' '.join(f"{k*0x400:#x}:{v:+d}" for k,v in sorted(net.items()) if v))
