import sys,re
L=open(sys.argv[1]).read().split('\n')
lo,hi=0x22a10+int(sys.argv[2],16),0x22a10+int(sys.argv[3],16)
on=False
for l in L:
    m=re.match(r'^([-+ ]) +(0x[0-9a-f]+)',l)
    if m and m.group(1) in '- ':
        a=int(m.group(2),16)
        if a>=lo: on=True
        if a>=hi: break
    if on: print(l)
