#!/usr/bin/env python3
# skel.py <dis> [lo] [hi] : CFG skeleton: branches, calls, exits, LINE/code stores, block labels
import sys,re
rows=[(int(l.split()[0],16),l.split(None,1)[1].strip()) for l in open(sys.argv[1])]
lo=int(sys.argv[2],16) if len(sys.argv)>2 else 0
hi=int(sys.argv[3],16) if len(sys.argv)>3 else 1<<30
tg=set()
for o,s in rows:
    m=re.search(r'@(0x[0-9a-f]+)$',s)
    if m: tg.add(int(m.group(1),16))
prev=None
for i,(o,s) in enumerate(rows):
    if not(lo<=o<hi): continue
    if o in tg or (prev and (prev.startswith('j') or prev.startswith('exit'))):
        print(f'{o:#06x}: ---- block')
    keep=s.startswith(('j','call','exit')) or re.match(r'stw \[r10 - 0x2b8\]',s) or re.match(r'stw \[r10 - 0x238\]',s)
    if keep:
        m=re.match(r'stw \[r10 - 0x2b8\], (0x[0-9a-f]+)',s)
        extra=f'   LINE {int(m.group(1),16)}' if m else ''
        m=re.match(r'stw \[r10 - 0x238\], (0x[0-9a-f]+)',s)
        extra+=f'   code {int(m.group(1),16)}' if m else ''
        # show the preceding compare context for conditional branches
        print(f'   {o:#06x}  {s}{extra}')
    prev=s
