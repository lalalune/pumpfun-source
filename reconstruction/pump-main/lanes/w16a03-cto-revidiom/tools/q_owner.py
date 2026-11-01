"""Find owner==&PROGRAM memcmp checks adjacent to data_is_empty calls in every original window; report order."""
import sys,os,collections
sys.path.insert(0,os.path.dirname(__file__))
import shape
from win_dm import dm
o=shape.orig(); ws={w[0]:w for w in shape.windows()}
# find data_is_empty target address: from main symbols
mrows,msyms=shape.main()
die=[a for a,n in msyms.items() if 'data_is_empty' in n]
print('data_is_empty syms',[hex(a) for a in die])
DIE=set(die)
def tgt(i):
    a,t,(mn,ops)=o[i]
    if mn=='call' and ops and ops[0][0]=='i': return a+8+ops[0][1]*8
res=collections.defaultdict(list)
for i in range(len(o)):
    if tgt(i) in DIE:
        # look back 12 insns for an owner memcmp: ldxdw x,[y+0x18] ... mov64 r3,0x20; call
        back=[o[k][1] for k in range(max(0,i-12),i)]
        fwd=[o[k][1] for k in range(i+1,min(len(o),i+12))]
        own_before=any('+ 0x18]' in b for b in back) and any('mov64 r3, 0x20' in b for b in back)
        own_after=any('+ 0x18]' in f for f in fwd) and any('mov64 r3, 0x20' in f for f in fwd)
        w=shape.win_of(o[i][0])
        if w: res[w[0]].append((o[i][0]-w[0],'owner->empty' if own_before else ('empty->owner' if own_after else 'empty-alone')))
names={w[0]:(w[2][0] if w[2] else 'admin_cto') for w in shape.windows()}
for w,v in sorted(res.items()):
    c=collections.Counter(x[1] for x in v)
    if c.get('owner->empty') or c.get('empty->owner'):
        print(f'{w:#08x} {dict(c)} {dm(names[w])[:90]}  ' + ' '.join(f'{a:#x}:{k[:5]}' for a,k in v if k!='empty-alone'))
