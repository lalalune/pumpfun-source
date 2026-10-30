import sys,re
# errs.py <disasm>: list (addr, line, code) error construction sites: stw [r10-0x2b8], line ; code from nearest stw [r10-0x238]
L=[l.rstrip() for l in open(sys.argv[1])]
for i,l in enumerate(L):
    m=re.match(r'(0x[0-9a-f]+)\s+stw \[r10 - 0x2b8\], (0x[0-9a-f]+)$',l)
    if m:
        code=None
        for j in range(max(0,i-40),min(len(L),i+40)):
            mm=re.search(r'stw \[r10 - 0x238\], (0x[0-9a-f]+)$',L[j])
            if mm and (code is None or abs(j-i)<abs(code[1]-i)): code=(mm.group(1),j)
        print(m.group(1), int(m.group(2),16), int(code[0],16) if code else None, 'line', i+1)
