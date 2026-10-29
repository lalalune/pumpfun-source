import sys;sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w4-sellv2-b/scripts')
import irlib
def edit(t):
    pre,parts,post=irlib.split(t)
    old="  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %quote_mint30.i, ptr noundef nonnull align 8 dereferenceable(32) %v291, i64 32, i1 false), !noalias !71464\n"
    new=''
    for k in range(4):
        new+=f"  %qs{k} = getelementptr inbounds i8, ptr %v291, i64 {8*k}\n  %ql{k} = load i64, ptr %qs{k}, align 8\n  %qd{k} = getelementptr inbounds i8, ptr %quote_mint30.i, i64 {8*k}\n  store i64 %ql{k}, ptr %qd{k}, align 1\n"
    for i,p in enumerate(parts):
        if old in p: parts[i]=p.replace(old,new)
    return irlib.join(pre,parts,post)
