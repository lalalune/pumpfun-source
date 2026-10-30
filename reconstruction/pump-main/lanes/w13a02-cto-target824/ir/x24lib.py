import re
ANCH_ALLOCA='  %holder_key = alloca [32 x i8], align 1'
T1_LAST=('  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(9) %target.sroa.8.0.target1.sroa_idx, '
         'ptr noundef nonnull align 1 dereferenceable(9) %target.sroa.8, i64 9, i1 false)\n')
BB74='bb74:                                             ; preds = %bb22\n'
PREP_CALL_RE=re.compile(r'  %_61 = getelementptr inbounds i8, ptr %_200, i64 48\n')
def start(): return '  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %x24)\n'
def end(): return '  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %x24)\n'
def wr(): return ('  %x24src = getelementptr inbounds i8, ptr %target1, i64 8\n'
                  '  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %x24, ptr noundef nonnull align 1 dereferenceable(24) %x24src, i64 24, i1 false)\n')
def rd(n='x24dst'): return (f'  %{n} = getelementptr inbounds i8, ptr %target1, i64 8\n'
                  f'  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(24) %{n}, ptr noundef nonnull align 8 dereferenceable(24) %x24, i64 24, i1 false)\n')
def base(t, anchor=ANCH_ALLOCA):
    assert t.count(anchor)==1, anchor
    return t.replace(anchor, '  %x24 = alloca [24 x i8], align 8\n'+anchor)
def at_t1(t, s):
    assert t.count(T1_LAST)==1
    return t.replace(T1_LAST, T1_LAST+s)
def at_bb74(t, s):
    assert t.count(BB74)==1
    i=t.index(BB74)+len(BB74)
    return t[:i]+s+t[i:]
LS_T0='  call void @llvm.lifetime.start.p0(i64 7, ptr nonnull %target.sroa.0)\n'
BB69_END=('  call void @llvm.lifetime.end.p0(i64 9, ptr nonnull %target.sroa.8)\n'
          '  call void @llvm.lifetime.end.p0(i64 48, ptr nonnull %st)\n'
          '  br label %bb65\n')
def at_blockstart(t, s):
    assert t.count(LS_T0)==1
    return t.replace(LS_T0, s+LS_T0)
def at_bb69(t, s):
    assert t.count(BB69_END)==1, t.count(BB69_END)
    return t.replace(BB69_END, s+BB69_END)
def sz(t, name, n):
    import re
    pat=re.compile(r'(  %'+re.escape(name)+r' = alloca )\[(\d+) x i8\], align (\d+)')
    m=pat.search(t); assert m, name
    al=max(int(m.group(3)),8) if n>=8 else int(m.group(3))
    return t[:m.start()]+f'{m.group(1)}[{n} x i8], align {al}'+t[m.end():]
