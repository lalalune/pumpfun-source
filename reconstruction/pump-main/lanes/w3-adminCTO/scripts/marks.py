import re,sys
for f in sys.argv[1:]:
    L=open(f).read().splitlines()
    base=int(L[0].split()[0],16)
    marks=[]
    for i,l in enumerate(L):
        ins=l.split(None,1)[1]
        if ins in ('mov64 r3, 0x150','mov64 r3, 0x180','mov64 r3, 0x120','mov64 r2, 0x37'): marks.append(hex(int(l.split()[0],16)-base)+':'+ins.split(', ')[1])
        if re.match(r'stw \[r10 - 0x[0-9a-f]+\], 0x(1[0-9a-f]{2}|2[0-9a-f]{2})$',ins): marks.append(hex(int(l.split()[0],16)-base)+':L'+str(int(ins.split(', ')[1],16)))
    print(f.split('/')[-1], ' '.join(marks))
