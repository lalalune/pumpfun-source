import sys,re
# jt.py file target_hex...: list jumps whose target is given offsets
L=[l.split(None,1) for l in open(sys.argv[1]) if len(l.split(None,1))>1]
tg=[int(x,16) for x in sys.argv[2:]]
for off,ins in L:
    o=int(off,16)
    m=re.match(r'(j\w+)\s.*?([+-]0x[0-9a-f]+|[+-]\d+)\s*(<.*>)?$',ins.strip())
    if m and not ins.startswith('call'):
        d=int(m.group(2),16) if '0x' in m.group(2) else int(m.group(2))
        t=o+8+d*8
        if t in tg: print(f"{off} {ins.strip()} -> {t:#x}")
