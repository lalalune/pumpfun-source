import sys,os,json
os.environ.setdefault('QBASE','s1')
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from q3 import *
def v4vol(pad=True,after=False):
    def f(b):
        m=re.search(r'  call void @llvm\.memcpy\.p0\.p0\.i64\(ptr align 1 (%_\d+), ptr align 1 %t, i64 32, i1 false\)\n',b)
        assert m,'no memcpy'
        a=m.group(0); d=m.group(1)
        P="  %newp = getelementptr inbounds i8, ptr %new, i64 1\n  %pk = load volatile i8, ptr %newp, align 1\n"
        new=f"  call void @llvm.memcpy.p0.p0.i64(ptr align 1 {d}, ptr align 1 %t, i64 32, i1 true)\n"
        if pad: new=(new+P) if after else (P+new)
        return b.replace(a,new,1)
    return lambda t:fnsub(t,VAL,f)
if __name__=='__main__':
    run('r7',[v4vol(True)])
    run('r8',[v4vol(False)])
    run('r9',[v4vol(True,True)])
