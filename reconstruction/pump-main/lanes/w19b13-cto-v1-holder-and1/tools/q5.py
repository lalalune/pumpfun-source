import sys,os,json
os.environ.setdefault('QBASE','s1')
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from q3 import *
def v4pre(k,ptvar=True):
    def f(b):
        a="  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_87, ptr align 1 %t, i64 32, i1 false)\n"
        if a not in b:
            # find the with_pubkeys first-arg copy from %t: pattern differs by gene numbering
            m=re.search(r'  call void @llvm\.memcpy\.p0\.p0\.i64\(ptr align 1 (%_\d+), ptr align 1 %t, i64 32, i1 false\)\n',b)
            assert m,'no memcpy'
            a=m.group(0); d=m.group(1)
        else: d='%_87'
        pad="  %%newp = getelementptr inbounds i8, ptr %%new, i64 1\n  %%pk = load volatile i8, ptr %%newp, align 1\n"
        pt="  %%tp1 = call noundef ptr @llvm.bpf.passthrough.p0.p0(i32 noundef zeroext 77, ptr noundef nonnull %%t)\n"
        return b.replace(a,(pad%())+(pt%()) + f"  call void @llvm.memcpy.p0.p0.i64(ptr align 1 {d}, ptr align 1 %tp1, i64 32, i1 false)\n",1)
    return lambda t:fnsub(t,VAL,f)
if __name__=='__main__':
    run('r6',[v4pre(0)])
