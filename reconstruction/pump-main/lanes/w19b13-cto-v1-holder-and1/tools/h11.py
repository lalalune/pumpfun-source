import sys,os,json,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
os.environ['KEEP']='0'
from h9 import *
from h6 import v4
def keep(t,where='after'):
    a="  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %_87.i, ptr noundef nonnull align 1 dereferenceable(32) %t.i, i64 32, i1 false)"
    assert t.count(a)==1
    i=t.index(a); j=t.index('\n',i)+1
    P="  %pn = load volatile i8, ptr %_61.sroa.5.0.new.sroa_idx, align 1\n"
    if where=='after': return t[:j]+P+t[j:]
    return t[:i]+P+t[i:]
if __name__=='__main__':
    for nm,f in [('w1',lambda t:keep(v4(t))),('w2',lambda t:keep(v4(t),'before')),('w3',lambda t:keep(v4(h7(t)))),('w4',lambda t:keep(v4(h7(t)),'before')),('w5',lambda t:keep(v4(tag1(h7(t)))))]:
        r=score(f(base),nm,ref='m1'); print(json.dumps(r)[:520],flush=True)
