import sys,re
# tgt.py listing.txt hexoff... : list branches targeting offsets (listing lines "0xADDR insn" or masked fn.txt)
L=[l for l in open(sys.argv[1]).read().splitlines() if l.strip()]
base=None; rows=[]
off=0
for l in L:
    p=l.split(None,1)
    if p[0].startswith('0x') and len(p)>1 and not p[0].startswith('0x') is False and re.match(r'0x[0-9a-f]+$',p[0]) and len(L[0].split()[0])>4:
        a=int(p[0],16); base=base if base is not None else a; o=a-base; s=p[1]
    else:
        o=off; s=l.strip()
    rows.append((o,s)); off=o+(16 if s.startswith('lddw') else 8)
want=[int(x,16) for x in sys.argv[2:]]
for o,s in rows:
    m=re.search(r'(j\w+).*?([+-]0x[0-9a-f]+)$',s)
    if m and s.startswith('j'):
        t=o+8+int(m.group(2),16)*8
        if not want or t in want: print(hex(o),s,'->',hex(t))
