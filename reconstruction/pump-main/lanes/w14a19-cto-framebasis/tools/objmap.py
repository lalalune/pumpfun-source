#!/usr/bin/env python3
"""objmap.py <xdir> [orig_fn] [--json out] : per-frame-object offset map of a candidate against the original.
Aligns frame-masked token streams (orig vs cand fn.txt), then for each aligned r10 access finds the candidate MIR
frame object containing it (xdir/frame.txt, r10 off == -MIR offset) and the delta orig_off - cand_off.
Reports: M (raw matched insns), masked M, per-object dominant delta and hit counts, and bounds:
  B_obj  = matched if every object were moved by its own dominant delta (perfect per-object relocation)
  B_spill= matched if the spill block (type spill-slot objects) moved by one uniform delta (+allocas unchanged)
  B_shift[d] best uniform shift of everything below a cut (one inserted/removed alloca) -> best (cut,d)."""
import sys,re,difflib,collections,json,os
X=sys.argv[1]; ORIG=sys.argv[2] if len(sys.argv)>2 and not sys.argv[2].startswith('-') else os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a19-cto-framebasis/orig_fn.txt')
def rd(f):
    A=[];T=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].strip(); A.append(s); s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw \1',s)
        s=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',s); s=re.sub(r'add64 (r\d), -0x[0-9a-f]+',r'add64 \1, -X',s); T.append(s)
    return A,T
oa,ot=rd(ORIG); ca,ct=rd(X+'/fn.txt')
objs=[]
for l in open(X+'/frame.txt'):
    p=l.split(); off=int(p[0],16); objs.append((off,int(p[1]),p[3]))
spill=set()
mir=open(X+'/pei.mir').read() if os.path.exists(X+'/pei.mir') else ''
for m in re.finditer(r"name: '', type: spill-slot, offset: (-?\d+)",mir): spill.add(-int(m.group(1)))
def obj(y):
    best=None
    for off,sz,n in objs:
        if off-sz< y <=off and (best is None or off<best[0]): best=(off,sz,n)
    return best
def off_of(s):
    m=re.search(r'r10 - (0x[0-9a-f]+)',s)
    if m: return int(m.group(1),16)
    m=re.search(r'add64 r\d, -(0x[0-9a-f]+)',s)
    return int(m.group(1),16) if m else None
sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False)
masked=sum(b.size for b in sm.get_matching_blocks())
pairs=[]; raw=0
for b in sm.get_matching_blocks():
    for k in range(b.size):
        o=oa[b.a+k]; c=ca[b.b+k]
        if o==c: raw+=1
        else:
            # same masked token, differs by offsets (or lddw/call operands)
            pass
        yo,yc=off_of(o),off_of(c)
        if yo is not None and yc is not None:
            pairs.append((yc,yo-yc,o.replace(hex(yo),'X')==c.replace(hex(yc),'X')))
per=collections.defaultdict(collections.Counter)
for yc,d,okshape in pairs:
    if not okshape: continue
    ob=obj(yc); key=ob if ob else (yc,0,'?')
    per[key][d]+=1
fixed_obj=sum(c.most_common(1)[0][1]-c.get(0,0) for c in per.values())
sp=collections.Counter()
for k,c in per.items():
    if k[0] in spill:
        for d,n in c.items(): sp[d]+=n
spill0=sp.get(0,0); spbest=sp.most_common(1)[0] if sp else (0,0)
# one cut shift: all objects with off>=cut (lower in memory, i.e. later FIs) move by d
cuts=sorted(set(k[0] for k in per))
best=(0,0,0)
for cut in cuts:
    tot=collections.Counter()
    for k,c in per.items():
        if k[0]>=cut:
            for d,n in c.items(): tot[d]+=n
    base=sum(c.get(0,0) for k,c in per.items() if k[0]>=cut)
    for d,n in tot.items():
        if d and n-base>best[0]: best=(n-base,cut,d)
res={'raw':raw,'masked':masked,'n':len(ct),'ratio':round(2*raw/(len(ot)+len(ct)),5),'frame_pairs':len(pairs),
     'frame_ok':sum(1 for yc,d,s in pairs if s and d==0),'B_obj_gain':fixed_obj,'spill_pairs':sum(sp.values()),'spill_ok':spill0,
     'spill_best_delta':spbest[0],'spill_best_n':spbest[1],'cut_gain':best[0],'cut_at':hex(best[1]),'cut_delta':best[2]}
print(json.dumps(res))
if '-v' in sys.argv:
    for k,c in sorted(per.items()):
        tot=sum(c.values())
        print(f"{k[0]:#06x} {k[1]:4d} {k[2][:22]:22s} {'S' if k[0] in spill else ' '} n={tot:3d} ok={c.get(0,0):3d} top={c.most_common(3)}")
