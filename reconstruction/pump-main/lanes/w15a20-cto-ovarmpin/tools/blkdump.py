import sys,re
p=sys.argv[1]; k=int(sys.argv[2]); names=sys.argv[3:]
t=open(p).read(); parts=re.split(r'^# \*\*\* IR Dump .*$',t,flags=re.M)
body=parts[k]
chunks=re.split(r'^(?=bb\.\d+)',body,flags=re.M)[1:]
for c in chunks:
    m=re.match(r'bb\.(\d+)(?:\.([^\s:(]+))?',c); n=m.group(2) or ''
    if any(n==x or re.fullmatch(x,n) for x in names): print(c.rstrip()[:3000]); print()
