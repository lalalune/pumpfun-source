#!/usr/bin/env python3
"""vpin.py <in.mir> <out.mir> %v=rN ...: rename a vreg to a physreg everywhere in execute and add liveins to every block
it is live into (computed by a backward dataflow over successors). ORACLE ONLY."""
import sys,re
src,dst=sys.argv[1:3]; pins=[a.split('=') for a in sys.argv[3:]]
L=open(src).read().split('\n')
f0=next(i for i,l in enumerate(L) if l.startswith('name:') and 'admin_cto7execute' in l)
f1=next((i for i in range(f0+1,len(L)) if L[i].startswith('name:')),len(L))
hdr={};order=[]
for i in range(f0,f1):
    m=re.match(r'^  bb\.(\d+)(\.\S*)?:',L[i])
    if m: hdr[int(m.group(1))]=i; order.append(int(m.group(1)))
end={b:(hdr[order[k+1]] if k+1<len(order) else f1) for k,b in enumerate(order)}
succ={}
for b in order:
    succ[b]=[]
    for i in range(hdr[b],end[b]):
        m=re.match(r'^\s+successors:(.*)$',L[i])
        if m: succ[b]=[int(x) for x in re.findall(r'%bb\.(\d+)',m.group(1))]; break
for v,R in pins:
    pat=re.compile(re.escape(v)+r'(?![\d])(:gpr)?')
    # per block: upward-exposed use? defines?
    ue={};df={}
    for b in order:
        u=False;d=False
        for i in range(hdr[b]+1,end[b]):
            l=L[i]
            if not pat.search(l): continue
            lhs,_,rhs=l.partition(' = ') if ' = ' in l else ('',None,l)
            if rhs is not None and pat.search(rhs) and not d: u=True
            if pat.search(lhs): d=True
        ue[b]=u; df[b]=d
    live={b:False for b in order}; ch=True
    while ch:
        ch=False
        for b in reversed(order):
            out=any(live[s] for s in succ[b]); li=ue[b] or (out and not df[b])
            if li!=live[b]: live[b]=li; ch=True
    for i in range(f0,f1): L[i]=pat.sub('$'+R,L[i]) if not L[i].lstrip().startswith('- {') else L[i]
    n=0
    for b in order:
        if live[b] and b!=order[0]:
            j=hdr[b]+1
            while re.match(r'^\s+successors:',L[j]): j+=1
            if re.match(r'^\s+liveins:',L[j]): L[j]=L[j].rstrip()+', $'+R
            else: L[j]='    liveins: $'+R+'\n'+L[j]
            n+=1
    print(f'pin {v}->${R}: live-in to {n} blocks',file=sys.stderr)
open(dst,'w').write('\n'.join(L))
