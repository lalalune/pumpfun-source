import sys; import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
def edit(t): return before(rm(t),'  %_205.not = icmp eq i8 %293, 0\n')
