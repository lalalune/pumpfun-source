import sys; import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
def edit(t): return after(rm(t),'  %_870 = getelementptr inbounds i8, ptr %_618, i64 648\n')
