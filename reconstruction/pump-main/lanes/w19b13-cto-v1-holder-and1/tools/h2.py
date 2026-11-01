import sys,os,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from h1 import *
CB="  %cashback.sroa.0.0.off0 = and i1 %_0.sroa.0.0.off0.i.not, %extract.t\n"
EX="  %extract.t = icmp ne i8 %v37, 0\n"
Z="  %v172 = zext i1 %cashback.sroa.0.0.off0 to i8\n"
def late(t):
    # p1 + weights: early and -3 gone, cashback at its use from the late and-1
    t=h7(t)
    t=rep(t,HE,''); t=rep(t,CB,'')
    t=rep(t,Z,"  %cashback.sroa.0.0.off0 = and i1 %nh1, %extract.t\n"+Z)
    return t
def late2(t):
    # cashback in bb6.i
    t=h7(t)
    t=rep(t,HE,''); t=rep(t,CB,'')
    t=rep(t,A1+B6,A1+"  %cashback.sroa.0.0.off0 = and i1 %nh1, %extract.t\n"+B6)
    return t
def late3(t):
    # cashback at use, extract.t at use too
    t=late(t); t=rep(t,EX,''); t=rep(t,"  %cashback.sroa.0.0.off0 = and i1 %nh1, %extract.t\n"+Z,EX+"  %cashback.sroa.0.0.off0 = and i1 %nh1, %extract.t\n"+Z); return t
def cb_arm(t):
    # cashback as a select at the join from the late and-1 in bb83 (validate join) instead of bb30
    t=h7(t)
    t=rep(t,HE,''); t=rep(t,CB,'')
    a="bb83:"
    i=t.index('\nbb83:'); j=t.index('\n',i+1)
    t=t[:j+1]+t[j+1:]
    # insert after phis of bb83: before first call in bb83
    k=t.index('  call void @llvm.memcpy',j)
    t=t[:k]+"  %cashback.sroa.0.0.off0 = and i1 %nh1, %extract.t\n"+t[k:]
    return t
if __name__=='__main__':
    v('h6',late)
    v('h7',late2)
    v('h8',late3)
    v('h9',cb_arm)
