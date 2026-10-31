# l1m.py a.bin b.bin lo hi : orig offsets in [lo,hi) matched at L1 in b but not in a (and vice versa counts), with b's matched cand offset
import sys,difflib,types
T='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a81-cto-s1colour/tools'
C=types.ModuleType('C'); _s=open(T+'/cls.py').read(); C.__dict__['__file__']=T+'/cls.py'; exec(_s[:_s.index('def main')],C.__dict__)
g={'__name__':'x'}; s_=open(T+'/rx.py').read(); exec(s_[:s_.index("OUT=os.environ.get")],g)
O=g['orig_window'](); OI=C.insns(O); lvl=int(sys.argv[5]) if len(sys.argv)>5 else 1
def mm(f):
    CI=C.insns(open(f,'rb').read()); sm=difflib.SequenceMatcher(None,[C.mask(t,lvl) for _,t in OI],[C.mask(t,lvl) for _,t in CI],autojunk=False); d={}
    for a,b,n in sm.get_matching_blocks():
        for k in range(n): d[OI[a+k][0]]=CI[b+k][0]
    return d
A=mm(sys.argv[1]); B=mm(sys.argv[2]); lo,hi=int(sys.argv[3],0),int(sys.argv[4],0)
onlyB=[o for o in B if lo<=o<hi and o not in A]; onlyA=[o for o in A if lo<=o<hi and o not in B]
print('onlyB',len(onlyB),'onlyA',len(onlyA))
import itertools
def runs(xs):
    xs=sorted(xs); out=[]
    for x in xs:
        if out and x-out[-1][1]==8: out[-1][1]=x
        else: out.append([x,x])
    return out
for r in runs(onlyB): print('B %04x-%04x n=%d cand %04x'%(r[0],r[1],(r[1]-r[0])//8+1,B[r[0]]))
for r in runs(onlyA): print('A %04x-%04x n=%d cand %04x'%(r[0],r[1],(r[1]-r[0])//8+1,A[r[0]]))
