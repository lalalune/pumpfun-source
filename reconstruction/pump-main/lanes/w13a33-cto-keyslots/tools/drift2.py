import sys,re,difflib
def norm(f):
    out=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',p[1].strip()); s=re.sub(r'<[^>]*>','',s).strip(); s=re.sub(r'[+-]0x[0-9a-f]+$','J',s)
        s=re.sub(r'\br\d\b','R',s)
        out.append((int(p[0],16),s))
    return out
a=norm(sys.argv[1]); b=norm(sys.argv[2])
sm=difflib.SequenceMatcher(None,[x[1] for x in a],[x[1] for x in b],autojunk=False)
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op!='equal' and (i2-i1)!=(j2-j1):
        print('%s a@%04x n=%d  b@%04x n=%d  delta %+d'%(op,a[i1][0] if i1<len(a) else -1,i2-i1,b[j1][0] if j1<len(b) else -1,j2-j1,(j2-j1)-(i2-i1)))
