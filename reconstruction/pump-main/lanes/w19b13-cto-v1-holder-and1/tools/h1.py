#!/usr/bin/env python3
"""h1.py: and-1 holder post-opt edits on new main (fx/m1/m.ll)"""
import sys,os,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from po import *
BASE=os.environ.get('H1BASE','m1')
base=rename(open(f'{OUT}/fx/{BASE}/m.ll').read())
W226='!226'
def find(t,s):
    assert t.count(s)==1,(t.count(s),s); return s
HE="  %v48 = and i8 %v0, -3\n  %_0.sroa.0.0.off0.i.not = icmp eq i8 %v48, 0\n"
B6="  %_21.not.i = icmp eq i8 %v35, 0\n  br i1 %_21.not.i, label %bb7.i, label %bb8.i\n"
A1="  %h1 = and i8 %v0, 1\n  %nh1 = icmp eq i8 %h1, 0\n"
T8="  br i1 %_0.sroa.0.0.off0.i.not, label %bb11.i, label %bb23.i\n"
T7="  br i1 %_0.sroa.0.0.off0.i.not, label %bb22.i, label %bb16.i, !prof !211\n"
T23="  br i1 %_0.sroa.0.0.off0.i.not, label %bb25, label %bb30\n"
def h7(t,w8=W226,w23=W226):
    t=rep(t,B6,A1+B6)
    t=rep(t,T8,T8.replace('%_0.sroa.0.0.off0.i.not','%nh1').rstrip('\n')+(f', !prof {w8}' if w8 else '')+'\n')
    t=rep(t,T7,T7.replace('%_0.sroa.0.0.off0.i.not','%nh1'))
    t=rep(t,T23,T23.replace('%_0.sroa.0.0.off0.i.not','%nh1').rstrip('\n')+(f', !prof {w23}' if w23 else '')+'\n')
    return t
def h7e(t,w8=W226,w23=W226):
    # and-1 early: replaces and -3 at the same place
    t=rep(t,HE,"  %v48 = and i8 %v0, 1\n  %_0.sroa.0.0.off0.i.not = icmp eq i8 %v48, 0\n")
    t=rep(t,T8,T8.rstrip('\n')+(f', !prof {w8}' if w8 else '')+'\n')
    t=rep(t,T23,T23.rstrip('\n')+(f', !prof {w23}' if w23 else '')+'\n')
    return t
def swap87(t):
    F=Fn(t); F.move_before('bb7.i','bb8.i'); return F.text()
def tag1(t):
    return rep(t,"  %trunc.not.i = icmp eq i8 %_61.sroa.0.0.copyload, 0\n","  %tand = and i8 %_61.sroa.0.0.copyload, 1\n  %trunc.not.i = icmp eq i8 %tand, 0\n")
def v(name,f,ref='m1'):
    t=f(base); r=score(t,name,ref=ref); print(json.dumps(r)[:560],flush=True); return r
if __name__=='__main__':
    v('h0',lambda t:t)
    v('h1',lambda t:h7(t))
    v('h2',lambda t:tag1(h7(t)))
    v('h3',lambda t:swap87(tag1(h7(t))))
    v('h4',lambda t:h7e(t))
    v('h5',lambda t:tag1(h7e(t)))
