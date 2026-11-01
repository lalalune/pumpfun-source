# w17a14 bba/bbb (black_box(&new)) with llvm.var.annotation in place of black_box, on main m3 (53ec7fb) slim IR
ANN=lambda p:f'  call void @llvm.var.annotation.p0.p0(ptr {p}, ptr null, ptr null, i32 0, ptr null)\n'
def entry(t):
    i=t.index('@_ZN14pump_recovered9admin_cto7execute17h'); j=t.index('start:\n',i)+len('start:\n')
    # after the allocas of the entry block
    k=j
    lines=t[j:].split('\n')
    n=0
    while ' = alloca ' in lines[n]: n+=1
    pos=j+sum(len(x)+1 for x in lines[:n])
    return t[:pos]+ANN('%new')+t[pos:]
import re
def after_args(t):
    m=re.search(r'  call void @llvm\.memcpy\.p0\.p0\.i64\(ptr align 1 (%_\d+), ptr align 1 %new, i64 33, i1 false\)\n',t)
    return t[:m.end()]+ANN('%new')+t[m.end():]
def before_validate(t):
    i=t.index('; call pump_recovered::admin_cto::validate\n')
    return t[:i]+ANN('%new')+t[i:]
V={'bbav':[entry],'bbbv':[after_args],'bbvv':[before_validate]}
