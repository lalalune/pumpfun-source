import sys,os,json,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from k1 import *
A="  %v49 = and i8 %v0, 1\n  %extract.t.not.i = icmp eq i8 %v49, 0\n"
def mv(where):
    def f(t):
        t=rep(t,A,'')
        i=t.index(where); return t[:i]+A+t[i:]
    return f
if __name__=='__main__':
    # candidates: just before the hr compare in bb5.i, and before lifetime markers
    v('a1',mv("  %_20.not.i = icmp eq i8 %v32, 0\n"))
    v('a2',mv("  %_7.not.i = icmp eq i8 %v47, 0\n"))
    v('a3',mv("  %extract.t = icmp ne i8 %v34, 0\n"))
