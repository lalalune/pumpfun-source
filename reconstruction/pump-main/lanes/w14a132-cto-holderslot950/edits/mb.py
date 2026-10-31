import sys,difflib,re
def rd(f):
    r=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=re.sub(r'<.*','',p[1]); s=re.sub(r'r\d','r',s); s=re.sub(r'[-+]0x[0-9a-f]+','',s)
        r.append((p[0],s.strip()))
    return r
a=rd(sys.argv[1]); b=rd(sys.argv[2]); mn=int(sys.argv[3]) if len(sys.argv)>3 else 20
sm=difflib.SequenceMatcher(None,[x[1] for x in a],[x[1] for x in b],autojunk=False)
for i,j,n in sm.get_matching_blocks():
    if n>=mn: print(a[i][0],b[j][0] if j<len(b) else '-',n, 'shift %+d'%((j-i)*8))
