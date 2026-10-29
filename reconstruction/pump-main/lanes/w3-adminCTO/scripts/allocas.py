import sys,re
t=open(sys.argv[1]).read().splitlines()
al=[]
for l in t[:400]:
    m=re.match(r'\s*(%\S+) = alloca \[(\d+) x i8\], align (\d+)',l)
    if m: al.append((m.group(1),int(m.group(2))))
body='\n'.join(t)
for i,(n,s) in enumerate(al):
    e=re.escape(n)
    lt=len(re.findall(r'lifetime\.start\.p0\(i64 \d+, ptr( nonnull)? '+e+r'\)',body))
    uses=len(re.findall(e+r'\b',body))-1
    print(f'fi#{i:3d} {n:40s} {s:4d} lt={lt} uses={uses}')
