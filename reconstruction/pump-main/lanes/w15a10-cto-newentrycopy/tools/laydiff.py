import sys,re,difflib
def rd(f):
    d=[]
    for l in open(f):
        p=l.split()
        if len(p)>=3: d.append((re.sub(r'\d+"?$','',p[2]),int(p[1]),p[0]))
    return d
a=rd(sys.argv[1]); b=rd(sys.argv[2])
sm=difflib.SequenceMatcher(None,[x[0] for x in a],[x[0] for x in b],autojunk=False)
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op=='equal':
        for i,j in zip(range(i1,i2),range(j1,j2)):
            if a[i][1]!=b[j][1]: print(f'~ {a[i][2]} {b[j][2]} {a[i][0][:60]:60s} {a[i][1]} -> {b[j][1]} ({b[j][1]-a[i][1]:+d})')
    else:
        print(op, 'A:',[(x[2],x[0][:40],x[1]) for x in a[i1:i2]][:8], 'B:',[(x[2],x[0][:40],x[1]) for x in b[j1:j2]][:8], 'sumA',sum(x[1] for x in a[i1:i2]),'sumB',sum(x[1] for x in b[j1:j2]))
