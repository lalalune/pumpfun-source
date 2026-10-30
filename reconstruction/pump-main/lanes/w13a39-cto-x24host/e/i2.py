EDITS=[("dereferenceable(7) %target.i.sroa.0, ptr noundef nonnull align 1 dereferenceable(7) %hk, i64 7","dereferenceable(7) %target.i.sroa.0, ptr noundef nonnull align 1 dereferenceable(7) %holder_key, i64 7"),
("dereferenceable(32) %hk, i64 32, i1 false)\n","dereferenceable(32) %hk, i64 32, i1 false)\n  call void @llvm.lifetime.end.p0(i64 33, ptr nonnull %hk)\n"),
lambda t: t.replace("  call void @llvm.lifetime.end.p0(i64 33, ptr nonnull %hk)\n  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %holder_key)\n","  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %holder_key)\n")]
