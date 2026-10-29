import sys,difflib,re,collections
def ab(l):
    l=re.sub(r'r\d+','r',l); l=re.sub(r'[-+]?0x[0-9a-f]+','N',l); l=re.sub(r'\b\d+\b','N',l); return l
o=open(sys.argv[1]).read().splitlines(); c=open(sys.argv[2]).read().splitlines()
sm=difflib.SequenceMatcher(None,[ab(x) for x in o],[ab(x) for x in c],autojunk=False)
off=collections.Counter(); regs=collections.Counter(); eq=0; tot=0; regdiff=0; offdiff=0; other=0
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag!='equal': continue
    for a,b in zip(o[i1:i2],c[j1:j2]):
        tot+=1
        if a==b: eq+=1; continue
        oa=re.findall(r'r10 - (0x[0-9a-f]+)',a); ob=re.findall(r'r10 - (0x[0-9a-f]+)',b)
        for x,y in zip(oa,ob):
            if x!=y: off[(x,y)]+=1
        ra=re.findall(r'r\d+',re.sub(r'r10','',a)); rb=re.findall(r'r\d+',re.sub(r'r10','',b))
        if ra!=rb: regdiff+=1
        if oa!=ob: offdiff+=1
print('aligned',tot,'equal',eq,'regdiff',regdiff,'offdiff',offdiff)
d=collections.Counter()
for (x,y),n in off.items(): d[int(y,16)-int(x,16)]+=n
print('offset deltas (cand-orig):',sorted(d.items(),key=lambda z:-z[1])[:10])
if len(sys.argv)>3:
  for (x,y),n in sorted(off.items()): print(x,y,n)
