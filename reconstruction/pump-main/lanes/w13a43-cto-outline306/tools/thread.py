import sys
# thread.py <raw.ll> <out.ll> <variant>: thread validate's holder tests (main a71238f raw IR line numbers)
src,out,v=sys.argv[1:4]
L=open(src).read().split('\n')
def rep(i,a,b):
    assert a in L[i],(i,L[i]); L[i]=L[i].replace(a,b)
# 0-based indices = line-1
rep(194599+1-1+1-1, '','') if False else None
idx={ 'bb9':194726, 'bb14':194600, 'bb15':194612, 'bb16':194618}
# find exact lines
def find(start,txt):
    for k in range(start,start+40):
        if L[k].strip()==txt: return k
    raise SystemExit('nf '+txt)
k=find(194724,'br label %bb21'); rep(k,'%bb21','%bb21h')
k=find(194614,'br i1 %_31, label %bb21, label %bb17'); rep(k,'label %bb21,','label %bb21h,')
if 'n' in v:
    k=find(194598,'br i1 %holder, label %bb15, label %bb21'); rep(k,'label %bb21','label %bb21n')
if 'h' in v:
    k=find(194610,'br i1 %_19, label %bb21, label %bb16'); rep(k,'label %bb21,','label %bb21h,')
k=find(194605,'br i1 %holder, label %bb22, label %bb23')
L.insert(k+1,'\nbb21h:\n  call void @llvm.lifetime.start.p0(i64 32, ptr %target)\n  br label %bb22\n\nbb21n:\n  call void @llvm.lifetime.start.p0(i64 32, ptr %target)\n  br label %bb23')
open(out,'w').write('\n'.join(L))
