import sys; import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
def edit(t):
    t=rm(t); a='  %.not = icmp eq i32 %298, 0\n  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %user)\n'
    assert t.count(a)==1; return t.replace(a,a+G,1)
