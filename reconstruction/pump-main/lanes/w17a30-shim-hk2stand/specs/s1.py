SKS=r'call void @llvm.lifetime.start.p0\(i64 32, ptr nonnull %skm\)$'
SKX=r'lifetime.start.p0\(i64 noundef 32, ptr noundef nonnull %skm\)'
SKW=r'dereferenceable\(32\) %skm, ptr noundef nonnull align 1 dereferenceable\(32\) %_458'
EOK=r'call void @llvm.lifetime.end.p0\(i64 32, ptr nonnull %skm\)'
S64=r'call void @llvm.lifetime.start.p0\(i64 16, ptr nonnull %_64.sroa.11\)'
M64=r'memcpy.p0.p0.i64\(ptr noundef nonnull align 8 dereferenceable\(9\) %_64.sroa.11'
base=[('S',SKS,0,'>'),('V',SKS,0,'>'),('E',EOK,0,'>'),('E',EOK,1,'>')]
SPECS=[]
# repair: move _64.sroa.11 START to its first use in bb82
rep=[('D',S64,0),('RAW',M64,0,'<','  call void @llvm.lifetime.start.p0(i64 16, ptr nonnull %_64.sroa.11)')]
SPECS.append(('r_only',{'size':32,'ops':rep}))
SPECS.append(('a1_rep',{'alloc':(r'^\s+%skm = alloca','<',32,8),'ops':base+rep}))
