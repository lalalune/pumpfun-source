import sys,re,difflib,collections
o=[l.strip() for l in open(sys.argv[1]) if l.strip()]; c=[l.strip() for l in open(sys.argv[2]) if l.strip()]
def M(s):
    s=re.sub(r'\br\d\b','r',s); s=re.sub(r'r10 - 0x[0-9a-f]+','S',s); s=re.sub(r'add64 r, -0x[0-9a-f]+','add64 r, S',s)
    return re.sub(r'[+-]0x[0-9a-f]+$','OFF',s) if s.startswith('j') else s
sm=difflib.SequenceMatcher(None,[M(x) for x in o],[M(x) for x in c],autojunk=False)
cnt=collections.Counter()
for tg,i1,i2,j1,j2 in sm.get_opcodes():
    if tg!='equal': continue
    for a,b in zip(o[i1:i2],c[j1:j2]):
        x=re.findall(r'r10 - (0x[0-9a-f]+)',a) or re.findall(r'add64 r\d, -(0x[0-9a-f]+)',a)
        y=re.findall(r'r10 - (0x[0-9a-f]+)',b) or re.findall(r'add64 r\d, -(0x[0-9a-f]+)',b)
        if x and y: cnt[(x[0],y[0])]+=1
bad=[(k,v) for k,v in cnt.items() if k[0]!=k[1]]
good=sum(v for k,v in cnt.items() if k[0]==k[1])
print('match',good,'mismatch',sum(v for k,v in bad))
for k,v in sorted(bad,key=lambda kv:-kv[1])[:40]: print(' orig',k[0],'cand',k[1],v)
