import sys,os,collections,difflib
sys.path.insert(0,os.path.dirname(__file__))
import shape,runs
from win_dm import dm
CTO=0x22a10
ws={w[0]:w for w in shape.windows()}
mrows,msyms=shape.main()
def targets(which):
    rows=shape.orig() if which=='orig' else mrows
    out=[]
    for a,t,(mn,ops) in rows:
        if CTO<=a<CTO+27400 and mn=='call':
            imm=ops[0][1]
            if t.startswith('call 0x') or t.startswith('call -0x'):
                # internal call: pc-relative in slots
                tgt=a+8+imm*8
                out.append((a-CTO,tgt))
            else: out.append((a-CTO,t))
    return out
o=targets('orig'); m=targets('main')
def name(t):
    if isinstance(t,str): return t
    w=ws.get(t)
    if w and w[2]: return dm(w[2][0])
    return msyms.get(t, hex(t))
on=[name(t) for a,t in o]; mn=[name(t) for a,t in m]
print(len(on),len(mn), 'multiset equal:', collections.Counter(on)==collections.Counter(mn))
sm=difflib.SequenceMatcher(None,on,mn,autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': print(f'= {i2-i1:3d}  orig {o[i1][0]:#06x}..{o[i2-1][0]:#06x}  main {m[j1][0]:#06x}..{m[j2-1][0]:#06x}')
    else:
        print(f'{tag} orig:'); [print(f'     {o[k][0]:#06x} {on[k][:110]}') for k in range(i1,i2)]
        print(f'  main:'); [print(f'     {m[k][0]:#06x} {mn[k][:110]}') for k in range(j1,j2)]
