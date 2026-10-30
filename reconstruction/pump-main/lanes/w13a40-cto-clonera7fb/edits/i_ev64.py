# IR probe: event/emit_cpi Err results (bb60) go straight to the final Err join bb64 instead of the signer_seeds
# cleanup join bb62, leaving bb62 with 2 preds (sharing CPI, pool CPI) -> the coalescer reaches the sweep Err copy
# block first (tie on pred+succ, lower block number). Models ending the signer_seeds temporaries before the event.
def edit(fn):
    b='  call void @llvm.lifetime.end.p0(i64 200, ptr nonnull %e)\n  br label %bb62\n'; assert fn.count(b)==1
    fn=fn.replace(b,'  call void @llvm.lifetime.end.p0(i64 200, ptr nonnull %e)\n  %pay60 = extractvalue { i64, ptr } %.pn, 1\n  br label %bb64\n')
    L=fn.split('\n')
    for k,l in enumerate(L):
        if l.startswith('  %.pn.pn.pn = phi'): L[k]=l.replace(', [ %.pn, %bb60 ]',''); assert L[k]!=l
        elif l.startswith('  %_0.sroa.0.3 = phi'): L[k]=l.replace(', [ %_0.sroa.0.1, %bb60 ]',''); assert L[k]!=l
        elif l.startswith('  %_0.sroa.11.4 = phi ptr'): L[k]=l.replace('phi ptr ','phi ptr [ %pay60, %bb60 ], ')
        elif l.startswith('  %_0.sroa.0.4 = phi i64'): L[k]=l.replace('phi i64 ','phi i64 [ %_0.sroa.0.1, %bb60 ], ')
    return '\n'.join(L)
