import re,sys
from dis import calls
def listing(show, which):
    r=[]
    for l in open(show):
        l=l.rstrip('\n')
        if l.startswith('- ') and which=='o':
            m=re.match(r'^- (0x[0-9a-f]+)\s+(.*)$',l); r.append((int(m.group(1),16),m.group(2)))
        elif l.startswith('+ ') and which=='c':
            m=re.match(r'^\+\s+(0x[0-9a-f]+)\s+(.*)$',l); r.append((int(m.group(1),16),m.group(2)))
        elif re.match(r'^  0x',l):
            m=re.match(r'^  (0x[0-9a-f]+) (0x[0-9a-f]+)\s+(.*)$',l)
            r.append((int(m.group(1 if which=='o' else 2),16),m.group(3)))
    return r
NAMES={0x157380:'name',0x15de88:'fmt',0x19bb30:'From',0xa938:'tostr',0x1b3678:'memcmp',0x19c1b8:'withpk',0x3cd50:'prepBC',0x1a2b38:'empty',0x1a7eb8:'findPDA',0x10c78:'clone'}
def annotate(lst,cl):
    cmap={a:t for a,t,_,_ in [(x[0]+0x22a10,x[1],0,0) for x in cl]}
    out=[]
    for i,(a,ins) in enumerate(lst):
        if a in cmap:
            t=cmap[a]; nm=NAMES.get(t,hex(t))
            line=code=None
            for j in range(i-1,max(0,i-40),-1):
                a2,ins2=lst[j]
                if ins2.startswith('call') : break
                m=re.match(r'stw \[r10 - 0x[0-9a-f]+\], (0x[0-9a-f]+)',ins2)
                if m:
                    v=int(m.group(1),16)
                    if 0x1770<=v<0x1a00 and code is None: code=v
                    elif 30<v<1200 and line is None: line=v
            out.append((a-0x22a10,nm,line,code))
    return out
if __name__=='__main__':
    show,orig,cand=sys.argv[1:4]
    o=annotate(listing(show,'o'),calls(orig)); c=annotate(listing(show,'c'),calls(cand))
    for i in range(max(len(o),len(c))):
        f=lambda x: '+%-5x %-7s L%-4s E%s'%(x[0],x[1],x[2],x[3]) if x else ''
        print('%3d %-34s | %s'%(i,f(o[i] if i<len(o) else None),f(c[i] if i<len(c) else None)))
