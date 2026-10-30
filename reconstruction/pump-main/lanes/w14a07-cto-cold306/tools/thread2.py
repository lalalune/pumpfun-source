import sys,re
# thread2.py <raw.ll> <out.ll> <variant x|n|nh|xn..>: thread validate's holder tests by block name (any main)
src,out,v=sys.argv[1:4]
L=open(src).read().split('\n')
S=next(i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto8validate' in l)
E=next(i for i in range(S,len(L)) if L[i]=='}')
def blk(name):
    k=next(i for i in range(S,E) if L[i].startswith(name+':'))
    return k
def rep(name,a,b):
    k=blk(name)
    while a not in L[k]: k+=1
    L[k]=L[k].replace(a,b,1)
rep('bb9','br label %bb21','br label %bb21h')
rep('bb16','label %bb21,','label %bb21h,')
if 'n' in v: rep('bb14','label %bb21','label %bb21n')
if 'h' in v: rep('bb15','label %bb21,','label %bb21h,')
k=blk('bb21')
L.insert(k,'bb21h:\n  call void @llvm.lifetime.start.p0(i64 32, ptr %target)\n  br label %bb22\n\nbb21n:\n  call void @llvm.lifetime.start.p0(i64 32, ptr %target)\n  br label %bb23\n')
open(out,'w').write('\n'.join(L))
