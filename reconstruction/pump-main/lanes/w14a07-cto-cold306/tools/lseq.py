import sys,re
# lseq.py fn.txt [maxaddr]: sequence of line immediates (stw ..., 0x11c..0x2ff) in address order
mx=int(sys.argv[2],16) if len(sys.argv)>2 else 1<<30
out=[]
for l in open(sys.argv[1]):
    p=l.split(None,1)
    if len(p)<2: continue
    a=int(p[0],16)
    if a>mx: break
    m=re.match(r'stw \[r10 - 0x[0-9a-f]+\], (0x[0-9a-f]+)$',p[1].strip())
    if m:
        v=int(m.group(1),16)
        if 270<=v<=780: out.append(f'{v}@{a:#x}')
print(' '.join(out))
