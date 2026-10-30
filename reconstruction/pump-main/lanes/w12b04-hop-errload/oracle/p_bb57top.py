import sys; import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
def edit(t): return after(rm(t),'  %_618 = load ptr, ptr %ctx.8.val, align 8, !nonnull !2, !align !3, !noundef !2\n')
