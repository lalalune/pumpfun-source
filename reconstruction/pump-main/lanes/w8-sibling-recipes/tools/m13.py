import sys,json
sys.path.insert(0,__file__.rsplit('/',1)[0])
import census as C
import fastmodel as F
import moves as MV
def model(so,ref): return F.Model(so,ref)
def p13(M,order): return MV.p16(M,order)
def aligned(M,order):
    fix=lambda a: M.wins[M.inv[a]]['bytes'] if M.inv[a] in M.UN else M.units[a][0]
    p=M.text0; n=0; pre=None
    for a in order:
        if a not in M.inv: continue
        if M.inv[a]==p: n+=1
        elif pre is None and M.region(a)=='L': pre=n
        p+=fix(a)
    return n,pre
def datamap(M,cand_path):
    cand=open(cand_path,'rb').read(); o,c=M.osec,M.csec; good={}
    for st,a,calls,tl,hd in M.checks:
        if not hd: good[st]=True; continue
        oo=C.operands(M.wins[st]['raw'],st,o); co=C.operands(C.body(cand,c,a,M.units[a][0]),a,c)
        d=[(x,y) for x,y in zip(oo,co) if x[1]=='lddw' and x[3]!='.text']
        good[st]=all(x[3]==y[3] and x[2]-o[x[3]]['addr']==y[2]-c[y[3]]['addr'] for x,y in d)
    return good
def p13real(M,order,good):
    fix=lambda a: M.wins[M.inv[a]]['bytes'] if M.inv[a] in M.UN else M.units[a][0]
    o=[a for a in order if a in M.inv]
    r=M.eval(o,fix,data_ok=True)
    return len([s for s in r if good[s]])
