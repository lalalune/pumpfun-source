import os
# fresh user/mint copies for the post call; PAIR=um|cq selects which pair takes the new allocas; POS = alloca after which new pair goes
def edit(t):
    pair=os.environ.get('PAIR','um'); pos=os.environ.get('POS','post_event')
    a="  %"+pos+" = alloca"; i=t.index(a); j=t.index('\n',i)+1
    t=t[:j]+"  %pA = alloca [32 x i8], align 1\n  %pB = alloca [32 x i8], align 1\n"+t[j:]
    old="""  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %_503, ptr noundef nonnull align 1 dereferenceable(32) %_984, i64 32, i1 false)
  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %_504)
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %_504, ptr noundef nonnull align 8 dereferenceable(32) %_692, i64 32, i1 false)"""
    assert old in t
    if pair=='um':  # user->pB? user,mint new allocas; curve/quote keep _503/_504
        U,M,C,Q='%pA','%pB','%_503','%_504'
    else:
        U,M,C,Q='%_503','%_504','%pA','%pB'
    if os.environ.get('SW'): U,M=M,U
    new=f"""  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %_504)
  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %pA)
  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %pB)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 {U}, ptr align 1 %_928, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 {M}, ptr align 1 %mint_key, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 {C}, ptr align 1 %_984, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 {Q}, ptr align 8 %_692, i64 32, i1 false)"""
    t=t.replace(old,new)
    oc="dereferenceable(32) %_451, ptr noalias nocapture noundef nonnull readonly align 1 dereferenceable(32) %_452, ptr noalias nocapture noundef nonnull readonly align 1 dereferenceable(32) %_503, ptr noalias nocapture noundef nonnull readonly align 1 dereferenceable(32) %_504,"
    assert oc in t
    t=t.replace(oc,f"dereferenceable(32) {U}, ptr noalias nocapture noundef nonnull readonly align 1 dereferenceable(32) {M}, ptr noalias nocapture noundef nonnull readonly align 1 dereferenceable(32) {C}, ptr noalias nocapture noundef nonnull readonly align 1 dereferenceable(32) {Q},")
    t=t.replace("  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %_504)\n  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %_503)\n","  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %pB)\n  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %pA)\n  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %_504)\n  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %_503)\n",1)
    return t
