def edit(t):
    old="""  %brmerge = or i1 %97, %partial_fill
  br i1 %brmerge, label %bb37, label %bb33

bb141:                                            ; preds = %bb31
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %_109)
  br i1 %partial_fill, label %bb37, label %bb33

bb37:                                             ; preds = %bb142, %bb141
  %can_cross.sroa.0.0.off0 = phi i1 [ false, %bb141 ], [ %97, %bb142 ]
"""
    new="""  br label %ccm

bb141:                                            ; preds = %bb31
  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %_109)
  br label %ccm

ccm:
  %can_cross.sroa.0.0.off0 = phi i1 [ false, %bb141 ], [ %97, %bb142 ]
  br i1 %can_cross.sroa.0.0.off0, label %bb37, label %ccp

ccp:
  br i1 %partial_fill, label %bb37, label %bb33

bb37:                                             ; preds = %ccm, %ccp
"""
    assert t.count(old)==1
    t=t.replace(old,new)
    return t
