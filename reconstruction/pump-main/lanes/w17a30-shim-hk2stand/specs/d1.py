import re
B=open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a30-shim-hk2stand/ir/exec_m0.ll').read().split('\n')
SKS=r'call void @llvm.lifetime.start.p0\(i64 32, ptr nonnull %skm\)$'
EOK=r'call void @llvm.lifetime.end.p0\(i64 32, ptr nonnull %skm\)'
X=[('S',SKS,0,'>'),('V',SKS,0,'>'),('E',EOK,0,'>'),('E',EOK,1,'>')]
AL=(r'^\s+%skm = alloca','<',32,8)
C1='bb14.i bb7.i bb10.i bb3.i30.i TS.exit31.i bb23.i bb30.i bb3.i37.i TS.exit38.i bb31.i bb16.i bb22.i bb17.i bb3.i23.i TS.exit24.i'
SPECS=[('d_base',{'alloc':AL,'ops':X,'order':C1,'w':'bb14.i:51:49'})]
seen={}
for i,l in enumerate(B):
    if i<225 or i>1010: continue
    if 'llvm.lifetime.' not in l: continue
    key=l.strip()
    rx='^'+re.escape(l)+'$'
    nth=sum(1 for x in B if x==l and B.index(x)<0)  # placeholder
    # nth = occurrence index of this exact line among identical lines before it
    k=seen.get(l,0); seen[l]=k+1
    m=re.search(r'%(\S+?)\)',l); nm=m.group(1) if m else '?'
    kind='S' if 'start' in l else 'E'
    SPECS.append((f'd_{kind}_{nm}_{i+1}',{'alloc':AL,'ops':X+[('D',rx,k)],'order':C1,'w':'bb14.i:51:49'}))
