import re,sys
def parse(p):
    L=[]
    for l in open(p).read().splitlines():
        a,b=l.split(None,1); L.append((int(a,16),b.split(' <')[0]))
    return L
def clones(p):
    L=parse(p); out=[]
    for i,(a,s) in enumerate(L):
        m=re.match(r'ldxdw (r\d), \[(r\d) \+ (0x[0-9a-f]+)\]$',s)
        if not m: continue
        rx=m.group(1)
        for j in range(i+1,min(i+4,len(L))):
            m2=re.match(r'ldxdw (r\d), \['+rx+r' \+ 0x8\]$',L[j][1])
            if m2:
                # check rc increment: next loads [m2+0]
                if any(re.match(r'ldxdw r\d, \['+m2.group(1)+r' \+ 0x0\]$',L[k][1]) for k in range(j+1,min(j+3,len(L)))):
                    out.append((a,m.group(3))); break
    return out
for p in sys.argv[1:]:
    c=clones(p); print(p,len(c)); print(' '.join(f'{o}' for a,o in c))
