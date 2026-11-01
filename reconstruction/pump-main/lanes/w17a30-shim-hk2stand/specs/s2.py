SKS=r'call void @llvm.lifetime.start.p0\(i64 32, ptr nonnull %skm\)$'
EOK=r'call void @llvm.lifetime.end.p0\(i64 32, ptr nonnull %skm\)'
S64=r'call void @llvm.lifetime.start.p0\(i64 16, ptr nonnull %_64.sroa.11\)'
M64=r'memcpy.p0.p0.i64\(ptr noundef nonnull align 8 dereferenceable\(9\) %_64.sroa.11'
X=[('S',SKS,0,'>'),('V',SKS,0,'>'),('E',EOK,0,'>'),('E',EOK,1,'>')]
REP=[('D',S64,0),('RAW',M64,0,'<','  call void @llvm.lifetime.start.p0(i64 16, ptr nonnull %_64.sroa.11)')]
AL=(r'^\s+%skm = alloca','<',32,8)
C1='bb14.i bb7.i bb10.i bb3.i30.i TS.exit31.i bb23.i bb30.i bb3.i37.i TS.exit38.i bb31.i bb16.i bb22.i bb17.i bb3.i23.i TS.exit24.i'
G1A='bb14.i bb23.i bb30.i bb3.i37.i TS.exit38.i'
SPECS=[]
for w in ['51:49','52:48','50:50']:
    SPECS.append((f'c1_{w}',{'ops':[],'order':C1,'w':f'bb14.i:{w}'}))
    SPECS.append((f'c1X_{w}',{'alloc':AL,'ops':X+REP,'order':C1,'w':f'bb14.i:{w}'}))
