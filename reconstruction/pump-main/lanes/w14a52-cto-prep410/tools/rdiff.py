import sys,re,difflib
exec(open('sl.py').read().split("lo,hi=")[0])
def rng(L,lo,hi): return [(a,t) for a,t in L if lo<=a<hi]
def m(t,lvl):
    t=re.sub(r'<[^>]*>','',t).strip()
    if lvl>=1: t=re.sub(r'r10 - 0x[0-9a-f]+','r10-F',t)
    if lvl>=2: t=re.sub(r'\br[0-9]\b','R',t)
    if lvl>=3: t=re.sub(r'([+-]0x[0-9a-f]+)$','J',t) if t.startswith(('j','ja')) else t
    return t
ol,oh,cl,ch,lvl=[int(x,16) for x in sys.argv[1:5]]+[int(sys.argv[5])]
O=rng(o,ol,oh); C=rng(c,cl,ch)
sm=difflib.SequenceMatcher(None,[m(t,lvl) for a,t in O],[m(t,lvl) for a,t in C],autojunk=False)
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op=='equal': print('  = %d insns  o%04x c%04x'%(i2-i1,O[i1][0],C[j1][0])); continue
    for k in range(max(i2-i1,j2-j1)):
        ot='%04x %-40s'%(O[i1+k][0],O[i1+k][1]) if i1+k<i2 else ' '*45
        ct='%04x %s'%(C[j1+k][0],C[j1+k][1]) if j1+k<j2 else ''
        print(op[0],ot,'|',ct)
print('ratio',round(sm.ratio(),4))
