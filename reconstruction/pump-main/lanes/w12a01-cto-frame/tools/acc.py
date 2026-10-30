#!/usr/bin/env python3
"""acc.py <so|orig> [lo hi]: list r10 accesses (offset, width, kind, addr) of admin_cto window, grouped by offset."""
import sys, collections, struct
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1].parent / 'w4-frame-oracle'))
av=sys.argv; sys.argv=av[:1]
import frameoracle as fo
sc=fo.load_score()
from pathlib import Path
src=av[1]; lo=int(av[2],16) if len(av)>2 else 0; hi=int(av[3],16) if len(av)>3 else 0x2000
if src=='orig':
    W={x['start']:x for x in sc.original_windows()}; raw=W[0x22a10]['raw']; base=0x22a10
else:
    cs=Path(src).read_bytes(); secs=sc.sections(cs)
    f=next(x for x in sc.candidate_functions(Path(src)) if 'admin_cto7execute' in x[2])
    raw=sc.body(cs,secs,f[0],f[1]); base=f[0]
W={0x61:4,0x69:2,0x71:1,0x79:8,0x63:4,0x6b:2,0x73:1,0x7b:8,0x62:4,0x6a:2,0x72:1,0x7a:8}
acc=collections.defaultdict(list)
for x in fo.decode(raw):
    so=fo.stack_off(x)
    if so is not None:
        k='L' if (x['op']&7)==1 else ('S' if (x['op']&7)==3 else 'I')
        acc[so].append((W.get(x['op'],0),k,base+x['i']))
    elif x['op']==0x07 and x['i']>=8:
        pass
# also lea: mov rX,r10 ; add rX,-imm
ins=fo.decode(raw); lea=collections.defaultdict(list)
for j in range(1,len(ins)):
    x=ins[j]; p=ins[j-1]
    if x['op']==0x07 and p['op']==0xbf and p['src']==10 and p['dst']==x['dst']:
        lea[-x['imm']].append(base+x['i'])
offs=sorted(set(acc)|set(lea))
for o in offs:
    if not (lo<=o<=hi): continue
    a=acc.get(o,[]); ws=collections.Counter((w,k) for w,k,_ in a)
    print(f'{o:#6x} ' + ' '.join(f'{k}{w}x{n}' for (w,k),n in sorted(ws.items())) + (f' LEA x{len(lea[o])}' if o in lea else '') +
          '  @' + ','.join(hex(ad) for _,_,ad in a[:4]) + (' lea@'+','.join(hex(ad) for ad in lea.get(o,[])[:3]) if o in lea else ''))
