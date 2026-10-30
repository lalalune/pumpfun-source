import sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from irre_lib import mask,orig,elf_fn
O=orig()
def hits(p):
    c=mask(elf_fn(p)); sm=difflib.SequenceMatcher(None,O,c,autojunk=False); h=[0]*len(O)
    for b in sm.get_matching_blocks():
        for k in range(b.size): h[b.a+k]=1
    # byte offsets per token
    off=[];x=0
    for t in O: off.append(x); x+=len(t)
    return h,off
rows=[]
for p in sys.argv[1:]:
    h,off=hits(p); per={}
    for i,v in enumerate(h): per[off[i]//0x800]=per.get(off[i]//0x800,0)+v
    rows.append((p.split('/')[-2],per,sum(h)))
ks=sorted(rows[0][1])
print('%-10s'%'', ' '.join('%5x'%(k*0x800) for k in ks),' total')
for n,per,t in rows: print('%-10s'%n[:10], ' '.join('%5d'%per.get(k,0) for k in ks), t)
