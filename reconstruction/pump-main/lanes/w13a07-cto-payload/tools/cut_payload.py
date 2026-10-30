#!/usr/bin/env python3
"""cut_payload.py in.ll out.ll [val|keep|p1p2]: emulate the original's 7/9-cut sharing payload (P1/P2) in main's IR.
place: where the four piece allocas go: 'val' (right after val.sroa.6.i), 'keep' (in place of the 32 B allocas)."""
import sys,re
s=open(sys.argv[1]).read(); place=sys.argv[3] if len(sys.argv)>3 else 'val'
if place=='p1p2': pass
nophi='nophi' in sys.argv[4:]
def rep(old,new,cnt=1):
    global s
    assert s.count(old)==cnt,(old,s.count(old)); s=s.replace(old,new)
A=lambda n,k:f'  %{n} = alloca [{k} x i8], align 1\n'
# allocas
rep('  %_401.sroa.6 = alloca [32 x i8], align 1\n','' if place=='val' else (A('p1a',7)+A('p1b',9)+(A('p2a',7)+A('p2b',9) if place=='p1p2' else '')))
rep('  %sharing_update.sroa.3 = alloca [32 x i8], align 1\n','' if place in ('val','p1p2') else A('p2a',7)+A('p2b',9))
if place=='val':
    rep('  %val.sroa.6.i = alloca [24 x i8], align 8\n','  %val.sroa.6.i = alloca [24 x i8], align 8\n'+A('p1a',7)+A('p1b',9)+A('p2a',7)+A('p2b',9))
# lifetime start
rep('  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %_401.sroa.6)\n','  call void @llvm.lifetime.start.p0(i64 7, ptr nonnull %p1a)\n  call void @llvm.lifetime.start.p0(i64 9, ptr nonnull %p1b)\n')
# arm copy from new
rep('  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %_401.sroa.6, ptr noundef nonnull align 1 dereferenceable(32) %_51.sroa.4.0.new.sroa_idx, i64 32, i1 false)\n',
'''  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %p1a, ptr align 1 %_51.sroa.4.0.new.sroa_idx, i64 7, i1 false)
  %nw8p = getelementptr inbounds i8, ptr %new, i64 8
  %nw8 = load i64, ptr %nw8p, align 1
  %nw16p = getelementptr inbounds i8, ptr %new, i64 16
  %nw16 = load i64, ptr %nw16p, align 1
  %nw24p = getelementptr inbounds i8, ptr %new, i64 24
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %p1b, ptr align 1 %nw24p, i64 9, i1 false)
''')
# join
rep('  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %sharing_update.sroa.3, ptr noundef nonnull align 1 dereferenceable(32) %_401.sroa.6, i64 32, i1 false)\n  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %_401.sroa.6)\n',
'''  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %p2a, ptr align 1 %p1a, i64 7, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %p2b, ptr align 1 %p1b, i64 9, i1 false)
  call void @llvm.lifetime.end.p0(i64 7, ptr nonnull %p1a)
  call void @llvm.lifetime.end.p0(i64 9, ptr nonnull %p1b)
''')
# phi must be first in block: move the two phis after the existing phis of bb22

# use
rep('  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %sharing_update.sroa.3.0.val6.sroa_idx, ptr noundef nonnull align 1 dereferenceable(32) %sharing_update.sroa.3, i64 32, i1 false)\n',
'''  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %sharing_update.sroa.3.0.val6.sroa_idx, ptr align 1 %p2a, i64 7, i1 false)
  %nw8p2 = getelementptr inbounds i8, ptr %new, i64 8
  %nw16p2 = getelementptr inbounds i8, ptr %new, i64 16
  %v8 = getelementptr inbounds i8, ptr %val6, i64 8
  %su8r = load i64, ptr %nw8p2, align 1
  store i64 %su8r, ptr %v8, align 1
  %v16 = getelementptr inbounds i8, ptr %val6, i64 16
  %su16r = load i64, ptr %nw16p2, align 1
  store i64 %su16r, ptr %v16, align 1
  %v24 = getelementptr inbounds i8, ptr %val6, i64 24
  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %v24, ptr align 1 %p2b, i64 9, i1 false)
''')
open(sys.argv[2],'w').write(s)
