#!/usr/bin/env python3
"""webs.py <dis> [--min-span N] [--json out]: CFG-aware reaching-definition webs of [r10-X] frame slots in a
win.py-style disassembly ("<hexoff> mnem ops"). A web = defs + uses linked by reaching defs on one exact offset.
Prints per web: slot, size set, def offsets, first/last use, span (bytes of linear code between first def and last use),
#uses, and the register stored at each def (to help name the value). Experiment / analysis only."""
import sys,re,json,collections
P=sys.argv[1]; a=sys.argv[2:]
mins=int(a[a.index('--min-span')+1],0) if '--min-span' in a else 0
L=[]
for l in open(P):
    m=re.match(r'\s*([0-9a-f]+)\s+(\w+)\s*(.*)$',l.strip())
    if m: L.append((int(m.group(1),16),m.group(2),m.group(3)))
idx={o:i for i,(o,_,_) in enumerate(L)}
import bisect,os
SY=[]
for l in open(os.environ.get('SYMS','/tmp/syms.txt')):
    x,sz,n=l.split(); SY.append((int(x,16),n))
SY.sort(); SK=[x[0] for x in SY]
def callee(i):
    o,mn,ops=L[i]; imm=int(ops,16)
    if imm>=2**31: imm-=2**32
    if imm==-1: return 'SYSCALL'
    t=0x22a10+o+8+imm*8; j=bisect.bisect_right(SK,t)-1
    return SY[j][1] if SY[j][0]==t else '?'
NORET=re.compile(r'unwrap_failed|panic|handle_alloc_error|abort|capacity_overflow|expect_failed')
def succ(i):
    o,mn,ops=L[i]
    if mn=='exit': return []
    if mn=='call' and NORET.search(callee(i)): return []
    # a relocated syscall without the sol_log_ (ptr,len) argument setup is abort() (Rc overflow): noreturn
    if mn=='call' and callee(i)=='SYSCALL' and not (L[i-1][1]=='mov64' and L[i-1][2].startswith('r2,')): return []
    if mn=='ja': return [idx[int(ops.split()[-1],16)]]
    if mn.startswith('j'):
        t=idx[int(ops.split(',')[-1].strip(),16)]; return [i+1,t]
    return [i+1] if i+1<len(L) else []
SZ={'dw':8,'w':4,'h':2,'b':1}
def acc(i):
    o,mn,ops=L[i]
    m=re.search(r'\[r10-0x([0-9a-f]+)\]',ops)
    if not m: return None
    off=int(m.group(1),16)
    if mn.startswith('ldx'): return ('u',off,SZ[mn[3:]],ops.split(',')[0].strip())
    if mn.startswith('stx'): return ('d',off,SZ[mn[3:]],ops.split(',')[-1].strip())
    if mn.startswith('st'): return ('d',off,SZ[mn[2:]],'imm '+ops.split(',')[-1].strip())
    return None
A={i:acc(i) for i in range(len(L))}
# reaching defs per offset (exact-offset tracking; a def of any size at off kills off)
offs=sorted({x[1] for x in A.values() if x})
S=[succ(i) for i in range(len(L))]
pred=collections.defaultdict(list)
for i,ss in enumerate(S):
    for j in ss: pred[j].append(i)
# dataflow: IN[i] = map off->set(def idx); iterate with worklist on instruction granularity (3.3k insns fine)
IN=[dict() for _ in L]; OUT=[dict() for _ in L]
work=collections.deque(range(len(L))); inq=set(work)
def tr(i,inm):
    x=A[i]
    if x and x[0]=='d':
        o=dict(inm); o[x[1]]=frozenset([i]); return o
    return inm
while work:
    i=work.popleft(); inq.discard(i)
    m={}
    for p in pred[i]:
        for k,v in OUT[p].items(): m[k]=m.get(k,frozenset())|v
    IN[i]=m; o=tr(i,m)
    if o!=OUT[i]:
        OUT[i]=o
        for j in S[i]:
            if j not in inq: work.append(j); inq.add(j)
# union-find webs
par={}
def f(x):
    while par.setdefault(x,x)!=x: par[x]=par[par[x]]; x=par[x]
    return x
def u(a,b): par[f(a)]=f(b)
uses=collections.defaultdict(list)
for i,x in A.items():
    if x and x[0]=='d': f(('d',i))
    if x and x[0]=='u':
        ds=IN[i].get(x[1],frozenset())
        f(('u',i))
        for d in ds: u(('u',i),('d',d))
        if not ds: u(('u',i),('ext',x[1]))
W=collections.defaultdict(list)
for k in list(par): W[f(k)].append(k)
rows=[]
for r,ms in W.items():
    ds=sorted(k[1] for k in ms if k[0]=='d'); us=sorted(k[1] for k in ms if k[0]=='u'); ext=any(k[0]=='ext' for k in ms)
    if not ds and not us: continue
    al=[A[i] for i in ds+us]; off=al[0][1]; sizes=sorted({x[2] for x in al})
    pos=[L[i][0] for i in ds+us]; lo=min(pos); hi=max(pos)
    rows.append(dict(off=off,sizes=sizes,defs=[hex(L[i][0]) for i in ds],dregs=[A[i][3] for i in ds],
                     uses=[hex(L[i][0]) for i in us],ext=ext,lo=lo,hi=hi,span=hi-lo,nu=len(us)))
rows.sort(key=lambda r:(r['off'],r['lo']))
if '--json' in a: json.dump(rows,open(a[a.index('--json')+1],'w'),indent=0)
for r in rows:
    if r['span']<mins: continue
    print(f"0x{r['off']:03x} sz{r['sizes']} span {r['lo']:#06x}-{r['hi']:#06x} ({r['span']:#x}) nu {r['nu']:2d} defs {','.join(r['defs'][:4])}{'..' if len(r['defs'])>4 else ''} dreg {','.join(r['dregs'][:3])}{' EXT' if r['ext'] else ''}")
if '--why' in a:
    off=int(a[a.index('--why')+1],16)
    for i,x in A.items():
        if x and x[0]=='u' and x[1]==off:
            print('use',hex(L[i][0]),L[i][1],L[i][2],'<-',[hex(L[d][0]) for d in sorted(IN[i].get(off,()))])
if '--path' in a:
    s0,t0=[idx[int(x,16)] for x in a[a.index('--path')+1].split(',')]
    off=int(a[a.index('--path')+2],16)
    prev={s0+1:s0}; q=collections.deque([s0+1])
    while q:
        i=q.popleft()
        if i==t0: break
        for j in S[i]:
            if j in prev: continue
            x=A[j]
            if x and x[0]=='d' and x[1]==off: continue
            prev[j]=i; q.append(j)
    p=[t0]
    while p[-1]!=s0: p.append(prev[p[-1]])
    p=p[::-1]
    for k,i in enumerate(p):
        if k==0 or p[k-1]!=i-1 or L[i][1]=='call': print(hex(L[i][0]),L[i][1],L[i][2], ('<-'+hex(L[p[k-1]][0])+' '+L[p[k-1]][1]+' '+L[p[k-1]][2]) if k else '', callee(i) if L[i][1]=='call' else '')
if '--per-def' in a:
    # Post-RA tail merging makes the CFG path-insensitively too permissive; assign each use to the nearest
    # preceding reaching def in address order (else the earliest reaching def) and report per-def intervals.
    D=collections.defaultdict(list)
    for i,x in A.items():
        if x and x[0]=='u':
            ds=sorted(IN[i].get(x[1],()))
            if not ds: continue
            pre=[d for d in ds if d<i]; d=max(pre) if pre else min(ds)
            D[d].append(i)
    out=[]
    for i,x in A.items():
        if x and x[0]=='d':
            us=D.get(i,[]); hi=max([L[j][0] for j in us],default=L[i][0])
            out.append(dict(off=x[1],sz=x[2],d=L[i][0],reg=x[3],uses=[L[j][0] for j in us],hi=hi,span=hi-L[i][0]))
    ms=int(a[a.index('--per-def')+1],0)
    json.dump(out,open(a[a.index('--per-def')+2],'w'))
    for r in sorted(out,key=lambda r:(r['off'],r['d'])):
        if r['span']>=ms and r['sz']==8: print(f"0x{r['off']:03x} def {r['d']:#06x} {r['reg']:6s} last {r['hi']:#06x} span {r['span']:#07x} nu {len(r['uses']):2d} uses {','.join(hex(u) for u in r['uses'][:6])}")
if '--live-at' in a:
    # backward slot liveness (exact offsets; any-size def kills); valid once noreturn calls end blocks (no cycles)
    pts=[int(x,16) for x in a[a.index('--live-at')+1].split(',')]
    LI=[frozenset() for _ in L]
    order=list(range(len(L)-1,-1,-1)); ch=True
    while ch:
        ch=False
        for i in order:
            lo=frozenset().union(*[LI[j] for j in S[i]]) if S[i] else frozenset()
            x=A[i]
            if x and x[0]=='d': lo=lo-{x[1]}
            if x and x[0]=='u': lo=lo|{x[1]}
            if lo!=LI[i]: LI[i]=lo; ch=True
    web={}
    for k in list(par): web.setdefault(f(k),[]).append(k)
    for p in pts:
        i=idx[p]; print(f'== live into {p:#x}:',len(LI[i]),'slots')
        for off in sorted(LI[i]):
            ds=sorted(IN[i].get(off,()))
            # later uses reachable: uses in the same web as these defs, positioned anywhere
            wk={f(('d',d)) for d in ds}
            us=sorted({L[k[1]][0] for w in wk for k in web[w] if k[0]=='u'})
            print(f"  0x{off:03x} defs {','.join(hex(L[d][0]) for d in ds)} dreg {','.join(A[d][3] for d in ds)} uses {','.join(hex(u) for u in us)}")
