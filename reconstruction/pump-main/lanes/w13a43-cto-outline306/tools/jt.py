import sys,re
# jt.py <disasm> <addr>... : list branches targeting addr
L=[l.rstrip() for l in open(sys.argv[1])]
tg={int(a,16) for a in sys.argv[2:]}
for l in L:
    m=re.match(r'(0x[0-9a-f]+)\s+(j\w+)\s+.*?([+-]0x[0-9a-f]+)$',l)
    if m:
        a=int(m.group(1),16); t=a+8+int(m.group(3),16)*8
        if t in tg: print(hex(t),'<-',l)
