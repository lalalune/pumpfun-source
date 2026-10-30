# IR probe (j3: bb62a kept non-empty by a volatile store): post-sweep Err join bb62 gets 2 preds (pool CPI + emit errors pre-joined in bb62a), so the
# coalescer (MBB priority = pred+succ count) visits the sweep Err copy block bb81 first.
def edit(fn):
    a='  br i1 %686, label %bb44, label %bb62\n'; assert fn.count(a)==1; fn=fn.replace(a,'  br i1 %686, label %bb44, label %bb62a\n')
    b='  call void @llvm.lifetime.end.p0(i64 200, ptr nonnull %e)\n  br label %bb62\n'; assert fn.count(b)==1
    fn=fn.replace(b,'  br label %bb62a\n\nbb62a:\n  %pnA = phi { i64, ptr } [ %684, %bb41 ], [ %.pn, %bb60 ]\n  %tgA = phi i64 [ %685, %bb41 ], [ %_0.sroa.0.1, %bb60 ]\n  store volatile i8 0, ptr %e, align 1\n  br label %bb62\n')
    c=[l for l in fn.split('\n') if l.startswith('  %.pn.pn.pn = phi')][0]
    c2=c.replace('[ %.pn, %bb60 ], [ %684, %bb41 ]','[ %pnA, %bb62a ]'); assert c2!=c; fn=fn.replace(c,c2)
    d=[l for l in fn.split('\n') if l.startswith('  %_0.sroa.0.3 = phi')][0]
    d2=d.replace('[ %_0.sroa.0.1, %bb60 ], [ %685, %bb41 ]','[ %tgA, %bb62a ]'); assert d2!=d; fn=fn.replace(d,d2)
    return fn
