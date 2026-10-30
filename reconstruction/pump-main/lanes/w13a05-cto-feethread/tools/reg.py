import sys,re,difflib
def load(f): return [(int(l.split()[0],16),l.split(None,1)[1].strip()) for l in open(f)]
def tok(s):
    s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw \1',s)
    s=re.sub(r'@0x[0-9a-f]+','@',s)
    s=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',s); s=re.sub(r'add64 (r\d+), -0x[0-9a-f]+',r'add64 \1, -X',s)
    return s
O=load('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w12a08-cto-errorder/an/orig.dis')
a=[tok(s) for o,s in O]
res=[]
for f in sys.argv[1:]:
    C=load(f); b=[tok(s) for o,s in C]
    sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
    m=[0]*len(a)
    for i,j,n in sm.get_matching_blocks():
        for k in range(n): m[i+k]=1
    row=[]
    for lo in range(0,0x6b00,0x800):
        sel=[x for (o,s),x in zip(O,m) if lo<=o<lo+0x800]
        row.append(sum(sel))
    res.append((f.split('/')[-2] if 'f.dis' in f else f.split('/')[-1],row,sm.ratio()))
print('region  '+' '.join('%5x'%lo for lo in range(0,0x6b00,0x800)))
for n,row,r in res: print('%-8s'%n[:8]+' '.join('%5d'%x for x in row)+'  %.4f'%r)
