#!/usr/bin/env python3
"""swr9.py <pre.mir> <out.mir> <vreg> <Jbb> [reg=r9] [mode=top]: force `swept` (vreg) into a physreg from the top of block
Jbb (the sweep-exit Ok join) to its uses: insert `$reg = COPY %vreg` at Jbb's top, rewrite every use of %vreg in blocks
dominated by Jbb to $reg, add `liveins: $reg` to every block on a path Jbb -> use. Pre-greedy MIR (-stop-before=greedy).
ORACLE ONLY (a physreg pin; not source)."""
import sys,re
src,dst,v,J=sys.argv[1:5]; R=sys.argv[5] if len(sys.argv)>5 else 'r9'
L=open(src).read().split('\n')
f0=next(i for i,l in enumerate(L) if l.startswith('name:') and 'admin_cto7execute' in l)
f1=next((i for i in range(f0+1,len(L)) if L[i].startswith('name:')),len(L))
hdr={}; order=[]
for i in range(f0,f1):
    m=re.match(r'^  bb\.(\d+)(\.\S*)?:',L[i])
    if m: hdr[int(m.group(1))]=i; order.append(int(m.group(1)))
end={}
for k,b in enumerate(order): end[b]=hdr[order[k+1]] if k+1<len(order) else f1
succ={}
for b in order:
    s=[]
    for i in range(hdr[b],end[b]):
        m=re.match(r'^\s+successors:(.*)$',L[i])
        if m: s=[int(x) for x in re.findall(r'%bb\.(\d+)',m.group(1))]; break
    # fallthrough (no successors line and no terminator) is not expected in this MIR
    succ[b]=s
pred={b:[] for b in order}
for b in order:
    for s in succ[b]: pred[s].append(b)
# dominators (iterative)
ent=order[0]; dom={b:set(order) for b in order}; dom[ent]={ent}; ch=True
while ch:
    ch=False
    for b in order:
        if b==ent: continue
        n=set(order)
        for p in pred[b]: n&=dom[p]
        n=n|{b} if pred[b] else {b}
        if n!=dom[b]: dom[b]=n; ch=True
DEFJ=[]; J=int(J); pat=re.compile(re.escape(v)+r'\b(?!:)')
useb=set(); nuse=0
for b in order:
    if J not in dom[b]: continue
    for i in range(hdr[b]+1,end[b]):
        if re.match(r'^\s+'+re.escape(v)+r':gpr = ',L[i]):
            if b!=J: sys.exit(f'def of {v} inside dominated region at line {i+1}: {L[i]}')
            DEFJ.append(i); continue
        if pat.search(L[i]): useb.add(b)
# blocks on a path J -> use block (reach J forward and reach a use block backward), within dom(J)
fw=set([J]); st=[J]
while st:
    x=st.pop()
    for s in succ[x]:
        if s not in fw and J in dom[s]: fw.add(s); st.append(s)
bw=set(useb); st=list(useb)
while st:
    x=st.pop()
    for p in pred[x]:
        if p not in bw and p in fw: bw.add(p); st.append(p)
live=(fw&bw)-{J}
out=list(L); ins={}
for b in order:
    if J not in dom[b]: continue
    for i in range(hdr[b]+1,end[b]):
        if i in DEFJ: out[i]=re.sub(r'^(\s+)'+re.escape(v)+r':gpr = ',r'\1$'+R+' = ',L[i]); continue
        if pat.search(L[i]) and not L[i].lstrip().startswith(('successors','liveins')):
            out[i]=pat.sub('$'+R,L[i]); nuse+=1
def body_start(b):
    i=hdr[b]+1
    while re.match(r'^\s+(successors|liveins):',L[i]) or L[i].strip()=='' : i+=1
    return i
for b in live:
    i=hdr[b]+1; j=i
    while re.match(r'^\s+successors:',L[j]): j+=1
    if re.match(r'^\s+liveins:',L[j]): out[j]=out[j].rstrip()+', $'+R
    else: ins.setdefault(j,[]).append('    liveins: $'+R)
(None if DEFJ else ins.setdefault(body_start(J),[]).append(f'    ${R} = COPY {v}'))
res=[]
for i,l in enumerate(out):
    if i in ins: res+=ins[i]
    res.append(l)
open(dst,'w').write('\n'.join(res))
print(f'swr9: {v} -> ${R} from bb.{J}: uses rewritten {nuse} in {len(useb)} blocks, liveins added to {len(live)} blocks',file=sys.stderr)
