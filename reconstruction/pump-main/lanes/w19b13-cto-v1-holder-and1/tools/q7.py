import sys,os,json
os.environ.setdefault('QBASE','s1')
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from q3 import *
def v4p(nfrom_t=3,order=(24,16,8,0)):
    """word copy of the with_pubkeys first key: the first nfrom_t words (in order) from the stack t, the rest from new+1"""
    def f(b):
        m=re.search(r'  call void @llvm\.memcpy\.p0\.p0\.i64\(ptr align 1 (%_\d+), ptr align 1 %t, i64 32, i1 false\)\n',b)
        assert m,'no memcpy'
        a=m.group(0); d=m.group(1); s=''
        for i,o in enumerate(order):
            if i<nfrom_t:
                s+=f"  %wa{o} = getelementptr inbounds i8, ptr %t, i64 {o}\n"
            else:
                s+=f"  %wa{o} = getelementptr inbounds i8, ptr %new, i64 {o+1}\n"
            s+=f"  %wv{o} = load i64, ptr %wa{o}, align 1\n  %wb{o} = getelementptr inbounds i8, ptr {d}, i64 {o}\n  store i64 %wv{o}, ptr %wb{o}, align 1\n"
        return b.replace(a,s,1)
    return lambda t:fnsub(t,VAL,f)
if __name__=='__main__':
    run('r10',[v4p(3)])
    run('r11',[v4p(4)])
    run('r12',[v4p(2)])
