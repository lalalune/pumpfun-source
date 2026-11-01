import re,sys
for f in sys.argv[1:]:
    L=[l.strip() for l in open(f)]
    out=[]
    for i in range(len(L)-1):
        a=re.search(r'ldxdw (r\d), \[r10([+-]\S+)\]',L[i]); b=re.search(r'stxdw \[r10([+-]\S+)\], (r\d)',L[i+1])
        if a and b and a.group(2)==b.group(1) and a.group(1)==b.group(2): out.append((L[i].split()[0],a.group(2)))
    print(f, out)
