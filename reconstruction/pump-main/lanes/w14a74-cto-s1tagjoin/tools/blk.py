import re,sys
log=open(sys.argv[1]).read().split('\n'); lo,hi=int(sys.argv[2]),int(sys.argv[3])
g=next(i for i,l in enumerate(log) if l.startswith('********** GREEDY'))
mi=next(i for i in range(g,0,-1) if log[i].startswith('********** MACHINEINSTRS'))
pre=log[mi:g]
for l in pre:
    m=re.match(r'(\d+)B\t(.*)',l)
    if not m: continue
    s=int(m.group(1))
    if lo<s<hi and (m.group(2).startswith('bb.') or 'JAL' in m.group(2)):
        t=m.group(2)
        if 'JAL' in t:
            p=t.split('@',1); t='   '+re.sub(r'17h[0-9a-f]+E.*','',p[1] if len(p)>1 else t)[-70:]
        print(s,t[:120])
