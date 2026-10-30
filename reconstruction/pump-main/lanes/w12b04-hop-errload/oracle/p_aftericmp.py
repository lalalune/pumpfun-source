import sys; import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
def edit(t): return after(rm(t),'  %.not = icmp eq i32 %298, 0\n')
