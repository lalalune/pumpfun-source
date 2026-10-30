import sys,re
f,lo,hi=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3],16)
rows=[(int(l.split()[0],16),l.split(None,1)[1].strip()) for l in open(f)]
targets=set()
for a,s in rows:
    m=re.search(r'@(0x[0-9a-f]+)$',s)
    if m: targets.add(int(m.group(1),16))
prev=None
for a,s in rows:
    if not lo<=a<hi: continue
    lab='*' if a in targets else ' '
    keep=s.startswith(('j','call','exit')) or re.match(r'stw \[r10 - 0x2b8\]',s) or re.search(r'and64 r\d, 0x1$',s) or re.match(r'ldxdw r\d, \[r10 - 0x9[0-9a-f]{2}\]',s) or re.match(r'ldxdw r\d, \[r10 - 0x8[c-f][0-9a-f]\]',s) or re.match(r'ldxb',s) or re.match(r'mov64 r\d, 0x[01]$',s)
    if keep or a in targets: print(f'{lab}{a:#06x}  {s}')
