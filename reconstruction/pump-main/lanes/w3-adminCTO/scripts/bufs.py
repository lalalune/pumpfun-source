import sys,re
L=[l.split(None,1) for l in open(sys.argv[1])]
st=int(L[0][0],16)
for i in range(len(L)-2):
    m=[re.match(r'stdw \[r10 - (0x[0-9a-f]+)\], (0x[0-9a-f]+)$',L[i+k][1].strip()) for k in range(3)]
    if all(m) and [x.group(2) for x in m]==['0x0','0x1','0x0']:
        o=[int(x.group(1),16) for x in m]
        if o[0]==o[1]-8==o[2]-16: print(hex(int(L[i][0],16)-st), 'buf@',hex(o[2]))
