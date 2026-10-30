#!/usr/bin/env python3
"""cut_entrycopy.py in.ll out.ll [opts]: emulate the original's entry copy of `new` (F7/G9 + two i64 at entry) and the
7/9-cut sharing payload P1 (arm) -> P2 (join) in main's IR.  opts: nop (no P1/P2 cut, entry copy only),
pval (P1/P2 allocas after val.sroa.6.i, default) | pkeep (in place), fpos=val6|holder"""
import sys,re
s=open(sys.argv[1]).read(); o=set(sys.argv[3:])
def rep(old,new,cnt=1):
    global s
    assert s.count(old)==cnt,(old[:120],s.count(old)); s=s.replace(old,new)
A=lambda n,k:f'  %{n} = alloca [{k} x i8], align 1\n'
cut='nop' not in o
# entry copy allocas
if 'fhold' in o: rep('  %holder_key = alloca','  %f7 = alloca [7 x i8], align 1\n  %g9 = alloca [9 x i8], align 1\n  %holder_key = alloca')
else: rep('  %val6 = alloca [33 x i8], align 1\n','  %val6 = alloca [33 x i8], align 1\n'+A('f7',7)+A('g9',9))
rep('  %cashback.sroa.0.0.off0 = and i1 %extract.t, %not._0.sroa.0.0.off0.i67\n','''  %cashback.sroa.0.0.off0 = and i1 %extract.t, %not._0.sroa.0.0.off0.i67
  call void @llvm.lifetime.start.p0(i64 7, ptr nonnull %f7)
  call void @llvm.lifetime.start.p0(i64 9, ptr nonnull %g9)
  %ntag = load i8, ptr %new, align 1, !range !394, !noundef !2
  %nw1p = getelementptr inbounds i8, ptr %new, i64 1
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %f7, ptr align 1 %nw1p, i64 7, i1 false)
  %nw8p = getelementptr inbounds i8, ptr %new, i64 8
  %nw8 = load i64, ptr %nw8p, align 1
  %nw16p = getelementptr inbounds i8, ptr %new, i64 16
  %nw16 = load ptr, ptr %nw16p, align 1
  %nw24p = getelementptr inbounds i8, ptr %new, i64 24
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %g9, ptr align 1 %nw24p, i64 9, i1 false)
''')
rep('  %81 = load i8, ptr %new, align 1, !range !394, !noundef !2\n','  %81 = add i8 %ntag, 0\n')
rep('  %82 = load i8, ptr %new, align 1, !range !394, !noundef !2\n','  %82 = add i8 %ntag, 0\n')
rep('  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %t.i, ptr noundef nonnull align 1 dereferenceable(32) %83, i64 32, i1 false), !noalias !5585\n',
'''  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %t.i, ptr align 1 %f7, i64 7, i1 false)
  %ti7 = getelementptr inbounds i8, ptr %t.i, i64 7
  store i64 %nw8, ptr %ti7, align 1
  %ti15 = getelementptr inbounds i8, ptr %t.i, i64 15
  store ptr %nw16, ptr %ti15, align 1
  %ti23 = getelementptr inbounds i8, ptr %t.i, i64 23
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %ti23, ptr align 1 %g9, i64 9, i1 false)
''')
rep('dereferenceable(7) %target.i.sroa.0, ptr noundef nonnull align 1 dereferenceable(7) %83, i64 7','dereferenceable(7) %target.i.sroa.0, ptr noundef nonnull align 1 dereferenceable(7) %f7, i64 7')
rep('  %target.i.sroa.7.0.copyload306 = load i64, ptr %target.i.sroa.7.0..sroa_idx, align 1, !noalias !5585\n','  %target.i.sroa.7.0.copyload306 = add i64 %nw8, 0\n')
rep('  %target.i.sroa.8.0.copyload307 = load ptr, ptr %target.i.sroa.8.0..sroa_idx, align 1, !noalias !5585\n','  %target.i.sroa.8.0.copyload307 = getelementptr i8, ptr %nw16, i64 0\n')
rep('dereferenceable(9) %target.i.sroa.9, ptr noundef nonnull align 1 dereferenceable(9) %target.i.sroa.9.0..sroa_idx, i64 9','dereferenceable(9) %target.i.sroa.9, ptr noundef nonnull align 1 dereferenceable(9) %g9, i64 9')
if cut:
    rep('  %_401.sroa.6 = alloca [32 x i8], align 1\n','' if 'pkeep' not in o else A('p1a',7)+A('p1b',9))
    rep('  %sharing_update.sroa.3 = alloca [32 x i8], align 1\n','' if 'pkeep' not in o else A('p2a',7)+A('p2b',9))
    if 'pkeep' not in o:
        rep('  %val.sroa.6.i = alloca [24 x i8], align 8\n','  %val.sroa.6.i = alloca [24 x i8], align 8\n'+A('p1a',7)+A('p1b',9)+A('p2a',7)+A('p2b',9))
    rep('  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %_401.sroa.6)\n','  call void @llvm.lifetime.start.p0(i64 7, ptr nonnull %p1a)\n  call void @llvm.lifetime.start.p0(i64 9, ptr nonnull %p1b)\n')
    rep('  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %_401.sroa.6, ptr noundef nonnull align 1 dereferenceable(32) %_51.sroa.4.0.new.sroa_idx, i64 32, i1 false)\n',
    '  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %p1a, ptr align 1 %f7, i64 7, i1 false)\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %p1b, ptr align 1 %g9, i64 9, i1 false)\n')
    rep('  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %sharing_update.sroa.3, ptr noundef nonnull align 1 dereferenceable(32) %_401.sroa.6, i64 32, i1 false)\n  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %_401.sroa.6)\n',
    '''  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %p2a, ptr align 1 %p1a, i64 7, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %p2b, ptr align 1 %p1b, i64 9, i1 false)
  call void @llvm.lifetime.end.p0(i64 7, ptr nonnull %p1a)
  call void @llvm.lifetime.end.p0(i64 9, ptr nonnull %p1b)
''')
    rep('  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %sharing_update.sroa.3.0.val6.sroa_idx, ptr noundef nonnull align 1 dereferenceable(32) %sharing_update.sroa.3, i64 32, i1 false)\n',
    '''  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %sharing_update.sroa.3.0.val6.sroa_idx, ptr align 1 %p2a, i64 7, i1 false)
  %v8 = getelementptr inbounds i8, ptr %val6, i64 8
  store i64 %nw8, ptr %v8, align 1
  %v16 = getelementptr inbounds i8, ptr %val6, i64 16
  store ptr %nw16, ptr %v16, align 1
  %v24 = getelementptr inbounds i8, ptr %val6, i64 24
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %v24, ptr align 1 %p2b, i64 9, i1 false)
''')
else:
    rep('dereferenceable(32) %_401.sroa.6, ptr noundef nonnull align 1 dereferenceable(32) %_51.sroa.4.0.new.sroa_idx','dereferenceable(32) %_401.sroa.6, ptr noundef nonnull align 1 dereferenceable(32) %nw1p')
open(sys.argv[2],'w').write(s)
