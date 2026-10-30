import sys,re
L=[l.split(None,1) for l in open(sys.argv[1])]
for i,(a,ins) in enumerate(L):
    m=re.match(r'mov64 r3, (0x[0-9a-f]+)$',ins.strip())
    if m and int(m.group(1),16)>=0x30 and i+1<len(L) and L[i+1][1].startswith('call'):
        ctx=[x[1].strip() for x in L[max(0,i-6):i]]
        r1=[c for c in ctx if c.startswith('add64 r1') or c.startswith('mov64 r1')]
        r2=[c for c in ctx if c.startswith('add64 r2') or c.startswith('mov64 r2')]
        print(a,m.group(1),r1[-1:] ,r2[-1:])
