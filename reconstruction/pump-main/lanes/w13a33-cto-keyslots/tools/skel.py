import sys,re,difflib,subprocess,os
def norm(f,regs=True,frame=True):
    out=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2 or not re.match(r'^(0x)?[0-9a-f]+$',p[0]): continue
        s=re.sub(r'<[^>]*>','',p[1]).strip()
        if s.startswith('call'): s='call'
        s=re.sub(r'^lddw (r\d+), .*',r'lddw \1',s)
        if frame: s=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',s)
        if regs: s=re.sub(r'\br\d\b','R',s)
        s=re.sub(r'(j\w+ .*?)[+-]0x[0-9a-f]+$',r'\1J',s); s=re.sub(r'^ja [+-]0x[0-9a-f]+','ja J',s)
        out.append(s)
    return out
o_all=sys.argv[1]
for c in sys.argv[2:]:
    r=[]
    for rg,fr in [(False,False),(False,True),(True,False),(True,True)]:
        a=norm(o_all,rg,fr); b=norm(c,rg,fr)
        r.append(round(difflib.SequenceMatcher(None,a,b,autojunk=False).ratio(),4))
    print(c,'plain',r[0],'frame-masked',r[1],'reg-masked',r[2],'both',r[3])
