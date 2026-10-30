import sys; import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
def edit(t): return before(rm(t),'  call void @llvm.lifetime.start.p0(i64 112, ptr nonnull %_217)\n')
