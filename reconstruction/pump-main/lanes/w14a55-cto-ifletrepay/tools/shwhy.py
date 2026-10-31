# shwhy.py fn.bin dele_off [add_off]: which candidate tokens become matched/unmatched under a synthetic shift
import sys,os,difflib
MYA=sys.argv[:]; T=os.path.dirname(os.path.abspath(__file__))
sys.argv=["x",MYA[1]]; src=open(T+'/shift.py').read().split("if __name__=='__main__':")[0]; exec(src)
def k_of(off):
    return next(k for k in range(len(ins)) if slot[k]*8==off)
d=k_of(int(MYA[2],16)) if MYA[2]!='-' else None; a=k_of(int(MYA[3],16)) if len(MYA)>3 else None
def mt(c):
    t=mask(c); sm=difflib.SequenceMatcher(None,OT,t,autojunk=False); s=set()
    for b in sm.get_matching_blocks():
        for i in range(b.size): s.add((b.a+i))
    return s
B=mt(build()); V=mt(build(a,d))
oo=[];x=0
for t in OT: oo.append(x); x+=len(t)
print('gained orig',[hex(oo[i]) for i in sorted(V-B)]); print('lost orig',[hex(oo[i]) for i in sorted(B-V)])
