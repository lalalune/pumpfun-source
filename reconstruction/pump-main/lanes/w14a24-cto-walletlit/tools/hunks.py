import sys,re,difflib
def rd(p,lo,hi):
    r=[]
    for l in open(p):
        q=l.split(None,1)
        if len(q)<2: continue
        a=int(q[0],16)
        if lo<=a<hi:
            s=re.sub(r'\s*<[^>]*>','',q[1]).strip()
            s='call' if s.startswith('call') else s
            r.append((a,s))
    return r
def n(s): s=re.sub(r'r\d+','r',s); s=re.sub(r'r10 - 0x[0-9a-f]+','FP',s); s=re.sub(r'([+-])0x[0-9a-f]+$',r'J',s) if s.startswith('j') else s; return s
lo,hi=int(sys.argv[3],16),int(sys.argv[4],16)
o=rd(sys.argv[1],lo,hi); c=rd(sys.argv[2],lo-int(sys.argv[5],16) if len(sys.argv)>5 else lo,hi)
sm=difflib.SequenceMatcher(None,[n(x[1]) for x in o],[n(x[1]) for x in c],autojunk=False)
print('ratio_norm',round(sm.ratio(),4))
for t,i1,i2,j1,j2 in sm.get_opcodes():
    if t=='equal': continue
    print('==',t,hex(o[i1][0]) if i1<len(o) else '-', hex(c[j1][0]) if j1<len(c) else '-')
    for k in range(i1,i2): print('  O %04x %s'%o[k])
    for k in range(j1,j2): print('  C %04x %s'%c[k])
