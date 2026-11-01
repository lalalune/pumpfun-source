import sys,os,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from po import *
base=rename(open(f'{OUT}/fx/c3p/m.ll').read())
HE="  %v45 = and i8 %v0, -3\n  %_0.sroa.0.0.off0.i.not = icmp eq i8 %v45, 0\n"
CB="  %cashback.sroa.0.0.off0 = and i1 %_0.sroa.0.0.off0.i.not, %extract.t\n"
EX="  %extract.t = icmp ne i8 %v34, 0\n"
Z="  %v176 = zext i1 %cashback.sroa.0.0.off0 to i8\n"
def v(name,f,ref='c3p'):
    t=f(base); r=score(t,name,ref=ref); print(json.dumps(r)[:560],flush=True); return r
def k1(t):
    t=rep(t,HE,''); t=rep(t,CB,'')
    return rep(t,Z,"  %cashback.sroa.0.0.off0 = and i1 %extract.t.not.i, %extract.t\n"+Z)
def k2(t):
    # early flag: not sunk: zext early
    t=rep(t,Z,''); return rep(t,CB,CB+Z)
if __name__=='__main__':
    v('k1',k1)
    v('k2',k2)
