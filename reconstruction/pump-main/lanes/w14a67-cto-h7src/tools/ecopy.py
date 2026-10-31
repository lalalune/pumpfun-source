#!/usr/bin/env python3
"""ecopy.py in.ll out.ll [7|79|79m]: IR oracle: entry copy of new's 7/9-byte pieces (and middle words for 79m) into fresh
allocas before the mayhem test; validate's non-holder arm (bb45.i) reads them. Oracle only."""
import sys
src,dst=sys.argv[1:3]; mode=sys.argv[3] if len(sys.argv)>3 else '79'
t=open(src).read(); L=t.split('\n')
ia=[k for k,l in enumerate(L) if l.startswith('  %target.sroa.0 = alloca')][0]
L.insert(ia,'  %nc7 = alloca [7 x i8], align 1'); 
if '9' in mode: L.insert(ia,'  %nc9 = alloca [9 x i8], align 1')
j=[k for k,l in enumerate(L) if 'call void @llvm.lifetime.start.p0(i64 9, ptr nonnull %target.sroa.8)' in l][0]
ins=['  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %nc7, ptr align 1 %_45.sroa.5.0.new.sroa_idx, i64 7, i1 false)']
if '9' in mode: ins+=['  %nc9src = getelementptr inbounds i8, ptr %new, i64 24','  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %nc9, ptr align 1 %nc9src, i64 9, i1 false)']
if 'm' in mode: ins+=['  %ncm8p = getelementptr inbounds i8, ptr %new, i64 8','  %ncm8 = load i64, ptr %ncm8p, align 1','  %ncm16p = getelementptr inbounds i8, ptr %new, i64 16','  %ncm16 = load ptr, ptr %ncm16p, align 1']
L[j:j]=ins
t='\n'.join(L)
k=t.index('\nbb45.i:'); e=t.index('\n\n',k+1); x=t[k:e]
x=x.replace('ptr noundef nonnull align 1 dereferenceable(7) %_45.sroa.5.0.new.sroa_idx, i64 7','ptr noundef nonnull align 1 dereferenceable(7) %nc7, i64 7',1)
if '9' in mode: x=x.replace('dereferenceable(9) %target.i.sroa.9.0..sroa_idx, i64 9','dereferenceable(9) %nc9, i64 9',1)
if 'm' in mode:
    import re
    x=re.sub(r'  %target.i.sroa.7.0.copyload277 = load i64, ptr %target.i.sroa.7.0..sroa_idx, align 1, !noalias !\d+','  %target.i.sroa.7.0.copyload277 = add i64 %ncm8, 0',x)
    x=re.sub(r'  %target.i.sroa.8.0.copyload278 = load ptr, ptr %target.i.sroa.8.0..sroa_idx, align 1, !noalias !\d+','  %target.i.sroa.8.0.copyload278 = getelementptr i8, ptr %ncm16, i64 0',x)
t=t[:k]+x+t[e:]
open(dst,'w').write(t)
