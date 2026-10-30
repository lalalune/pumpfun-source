import sys,re
f,lo,hi=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3],16)
rows=[]
for l in open(f):
    for m in re.finditer(r'r10 - (0x[0-9a-f]+)',l):
        o=int(m.group(1),16)
        if lo<=o<hi: rows.append((o,l.strip()))
    m=re.search(r'add64 (r\d), -(0x[0-9a-f]+)',l)
    if m and lo<=int(m.group(2),16)<hi: rows.append((int(m.group(2),16),l.strip()+'   [addr]'))
for o,l in sorted(rows,key=lambda x:(-x[0])): print(hex(o),'|',l)
