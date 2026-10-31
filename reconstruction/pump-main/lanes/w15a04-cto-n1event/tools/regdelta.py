# regdelta.py cand.bin [lvl]: L-masked alignment vs orig; per orig call-index segment net instruction delta (orig - cand)
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import importlib.util
src=open(T+'/cls.py').read(); g={'__file__':T+'/cls.py','__name__':'x'}; exec(src[:src.index('def main')],g)
O=open(T+'/../orig.bin','rb').read(); C=open(sys.argv[1],'rb').read(); lvl=int(sys.argv[2]) if len(sys.argv)>2 else 3
oi=g['insns'](O); ci=g['insns'](C)
ot=[g['mask'](t,lvl) for _,t in oi]; ct=[g['mask'](t,lvl) for _,t in ci]
sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False)
# segment by orig call index
oc=[k for k,(o,t) in enumerate(oi) if t[0]==0x85]
def seg(k): return sum(1 for x in oc if x<k)
D={}
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op=='equal': continue
    s=seg(i1); D.setdefault(s,[0,0,oi[min(i1,len(oi)-1)][0]]); D[s][0]+=i2-i1; D[s][1]+=j2-j1
tot=0
for s in sorted(D):
    a,b,off=D[s]; tot+=a-b
    if a!=b: print('seg %3d @%05x orig-only %3d cand-only %3d net %+d  cum %+d'%(s,off,a,b,a-b,tot))
print('ratio L%d'%lvl, round(sm.ratio(),5), 'len',len(ot),len(ct))
