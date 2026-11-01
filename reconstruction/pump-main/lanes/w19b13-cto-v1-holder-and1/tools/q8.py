import sys,os,json
os.environ.setdefault('QBASE','s1')
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from q3 import *
def v4m(order='A',lo=8):
    def f(b):
        m=re.search(r'  call void @llvm\.memcpy\.p0\.p0\.i64\(ptr align 1 (%_\d+), ptr align 1 %t, i64 32, i1 false\)\n',b)
        assert m,'no memcpy'
        a=m.group(0); d=m.group(1)
        M=f"  %wa = getelementptr inbounds i8, ptr %t, i64 {lo}\n  %wb = getelementptr inbounds i8, ptr {d}, i64 {lo}\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %wb, ptr align 1 %wa, i64 {32-lo}, i1 false)\n"
        W=f"  %wn = getelementptr inbounds i8, ptr %new, i64 1\n  %wv = load i64, ptr %wn, align 1\n  store i64 %wv, ptr {d}, align 1\n"
        return b.replace(a,(M+W) if order=='A' else (W+M),1)
    return lambda t:fnsub(t,VAL,f)
if __name__=='__main__':
    run('r13',[v4m('A')])
    run('r14',[v4m('B')])
