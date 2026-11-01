SKS=r'call void @llvm.lifetime.start.p0\(i64 32, ptr nonnull %skm\)$'
EOK=r'call void @llvm.lifetime.end.p0\(i64 32, ptr nonnull %skm\)'
S64=r'call void @llvm.lifetime.start.p0\(i64 16, ptr nonnull %_67.sroa.11\)'
M64=r'memcpy.p0.p0.i64\(ptr noundef nonnull align 8 dereferenceable\(9\) %_67.sroa.11'
X=[('S',SKS,0,'>'),('V',SKS,0,'>'),('E',EOK,0,'>'),('E',EOK,1,'>')]
REP=[('D',S64,0),('RAW',M64,0,'<','  call void @llvm.lifetime.start.p0(i64 16, ptr nonnull %_67.sroa.11)')]
AL=(r'^\s+%skm = alloca','<',32,8)
SPECS=[('wn',{'ops':[]}),('wX',{'alloc':AL,'ops':X}),('wXr',{'alloc':AL,'ops':X+REP}),('wr',{'ops':REP})]
