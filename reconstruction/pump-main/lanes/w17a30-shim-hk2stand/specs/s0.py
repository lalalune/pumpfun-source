SKS=r'call void @llvm.lifetime.start.p0\(i64 32, ptr nonnull %skm\)$'   # bb13 head, rustc StorageLive(skm)
SKX=r'lifetime.start.p0\(i64 noundef 32, ptr noundef nonnull %skm\)'   # explicit lts before the st copy
SKW=r'dereferenceable\(32\) %skm, ptr noundef nonnull align 1 dereferenceable\(32\) %_458'  # sk write
VST=r'load volatile i8, ptr %hkx'                                         # validate top placeholder (nth 0)
EOK=r'call void @llvm.lifetime.end.p0\(i64 32, ptr nonnull %skm\)'      # nth 0 = bb81 (Err), nth 1 = bb30 (Ok)
A_SKM=(r'^\s+%skm = alloca',)
SPECS=[('m0',{'size':32,'ops':[]})]
for pos in ['skm','_33','st','_21','_303','dest.i','_11.i306']:
    for sz in [32]:
        SPECS.append((f'a1_{pos}_{sz}',{'alloc':(rf'^\s+%{pos} = alloca','<',sz,8),'ops':[('S',SKS,0,'>'),('V',SKS,0,'>'),('E',EOK,0,'>'),('E',EOK,1,'>')]}))
