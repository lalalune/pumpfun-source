import sys,os,json,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from h1 import *
def v4(t):
    # 307 with_pubkeys first key from the t stack slot, not forwarded from new+1
    a="(32) %_87.i, ptr noundef nonnull align 1 dereferenceable(32) %_61.sroa.5.0.new.sroa_idx, i64 32, i1 false)"
    return rep(t,a,"(32) %_87.i, ptr noundef nonnull align 1 dereferenceable(32) %t.i, i64 32, i1 false)")
if __name__=='__main__':
    r=v('v4a',lambda t:v4(h7(t)))
    r=v('v4b',lambda t:v4(t))
