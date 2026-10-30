import runpy
ss=runpy.run_path('ed/ir_sel_swap.py')['edit']
A='''  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %val8.sroa.2, ptr noundef nonnull align 8 dereferenceable(24) %_85.sroa.40, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_85.sroa.40)
  store ptr %_85.sroa.27.3155, ptr %quote_mint, align 8
  %val8.sroa.2.0.quote_mint.sroa_idx = getelementptr inbounds i8, ptr %quote_mint, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %val8.sroa.2.0.quote_mint.sroa_idx, ptr noundef nonnull align 8 dereferenceable(24) %val8.sroa.2, i64 24, i1 false)
'''
B='''  store ptr %_85.sroa.27.3155, ptr %quote_mint, align 8
  %val8.sroa.2.0.quote_mint.sroa_idx = getelementptr inbounds i8, ptr %quote_mint, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %val8.sroa.2.0.quote_mint.sroa_idx, ptr noundef nonnull align 8 dereferenceable(24) %_85.sroa.40, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_85.sroa.40)
'''
def edit(t):
    t=ss(t); assert t.count(A)==1; return t.replace(A,B)
