"""Query 1: classify every AccountInfo clone (Rc strong inc of lamports: ldxdw c,[b+8]; ldxdw d,[c+0]; add64 d,1)
by how the account pointer's container was obtained."""
import sys,os,collections
sys.path.insert(0,os.path.dirname(__file__))
import shape
o=shape.orig()
idx={a:i for i,(a,t,p) in enumerate(o)}
def defs_back(i, reg, lim=40, lo=None):
    """find the most recent def of reg before instruction i (within window lo)"""
    for j in range(i-1, max(i-lim, lo if lo is not None else 0)-1, -1):
        mn,ops=o[j][2]
        if ops and ops[0][0]=='r' and ops[0][1]==reg and not mn.startswith(('st','j','call')):
            return j
        if mn=='call' and reg<=5: return ('call',j)
    return None
res=[]
for i in range(len(o)-3):
    a,t,(mn,ops)=o[i]
    if mn!='ldxdw' or ops[1][0]!='m' or ops[1][2]!=8 or ops[1][1]==10: continue
    c=ops[0][1]; b=ops[1][1]
    # next few insns: ldxdw d,[c+0]; add64 d,1
    ok=False
    for k in range(i+1,min(i+4,len(o)-1)):
        mn2,ops2=o[k][2]
        if mn2=='ldxdw' and ops2[1][0]=='m' and ops2[1][1]==c and ops2[1][2]==0:
            d=ops2[0][1]; mn3,ops3=o[k+1][2]
            if mn3=='add64' and ops3[0]==('r',d) and ops3[1]==('i',1): ok=True
            break
    if not ok: continue
    w=shape.win_of(a)
    if not w: continue
    lo=idx.get(w[0],0)
    jb=defs_back(i,b,lo=lo)
    cls='?'; detail=''
    if isinstance(jb,int):
        mnb,opsb=o[jb][2]
        detail=o[jb][1]
        if mnb=='ldxdw' and opsb[1][0]=='m':
            base=opsb[1][1]
            if base==10: cls='B_from_fp'   # account ptr itself reloaded from stack
            else:
                ja_=defs_back(jb,base,lo=lo)
                if isinstance(ja_,int):
                    mna,opsa=o[ja_][2]
                    if mna=='ldxdw' and opsa[1][0]=='m' and opsa[1][1]==10:
                        cls='A_reload_fp' if jb-ja_<=2 else 'A_fp_far'
                        detail=o[ja_][1]+' ; '+o[jb][1]+f' (gap {jb-ja_})'
                    else:
                        cls='A_held'; detail=o[ja_][1]+' ; '+o[jb][1]+f' (gap {jb-ja_})'
                else: cls='A_none'
        else: cls='B_other'
    else: cls='B_none'
    res.append((w[0],a,cls,detail,w[2][:1]))
by=collections.defaultdict(collections.Counter)
for w,a,cls,d,s in res: by[w][cls]+=1
import json
names={}
for w in shape.windows(): names[w[0]]=(w[2][0] if w[2] else '?')
rows=[]
for w,c in by.items():
    n=sum(c.values()); r=c['A_reload_fp']
    rows.append((r,n,w,dict(c)))
rows.sort(key=lambda x:(-x[0],-x[1]))
from win_dm import dm
for r,n,w,c in rows[:60]:
    print(f'{w:#08x} reload {r:2d}/{n:2d} {c}  {dm(names.get(w,"?"))[:110]}')
if len(sys.argv)>1:
    W=int(sys.argv[1],16)
    for w,a,cls,d,s in res:
        if w==W: print(f'  {a-W:#06x} {cls:12s} {d}')
