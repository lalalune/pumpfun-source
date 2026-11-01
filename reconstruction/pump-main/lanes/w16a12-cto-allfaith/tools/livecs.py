#!/usr/bin/env python3
"""livecs.py <pei.mir> [--fn execute]: callee-saved (r6-r9) register occupancy at the admin_cto tail program points
(experiment only, no build). Parses the post-PEI MIR of admin_cto::execute, runs instruction-level liveness and
reaching definitions for r6..r9, and at each point prints, per live register, its reaching defs (MIR text) and whether
each def lies before the prepare_bonding_curve call (a head-to-tail value) or after it.
Points: sweep (2nd find_program_address), tcf (transfer_creator_fees_to_pump_v2), shcpi (admin_cto_sharing_config),
poolgate (last data_is_empty before admin_cto_pool), pool (admin_cto_pool)."""
import sys,re,collections,json
P=sys.argv[1]
t=open(P).read()
i=t.index('name:            _ZN14pump_recovered9admin_cto7execute')
j=t.find('\n---',i); t=t[i:j if j>0 else len(t)]
body=t[t.index('\nbody:'):]
blocks=[];cur=None
for l in body.splitlines():
    m=re.match(r'\s{2}bb\.(\d+)(?:\.([\w.]+))?.*:$',l)
    if m: cur={'id':int(m.group(1)),'name':m.group(2) or '','succ':[],'ins':[]}; blocks.append(cur); continue
    if cur is None: continue
    s=l.strip()
    if not s or s.startswith(';'): continue
    if s.startswith('successors:'): cur['succ']=[int(x) for x in re.findall(r'%bb\.(\d+)',s)]; continue
    if s.startswith('liveins:'): continue
    cur['ins'].append(s)
bid={b['id']:k for k,b in enumerate(blocks)}
# fallthrough: MIR lists successors explicitly, so use the successors line only
CS=('r6','r7','r8','r9')
def du(s):
    if ' = ' in s and not s.startswith('JAL'):
        lhs,rhs=s.split(' = ',1)
        d={r for r in re.findall(r'\$(r\d+)',lhs)}
    else: d=set(); rhs=s
    u=set()
    for m in re.finditer(r'(implicit-def\s+(?:dead\s+)?|implicit\s+(?:killed\s+)?)?\$(r\d+)',rhs):
        if m.group(1) and m.group(1).startswith('implicit-def'): d.add(m.group(2))
        else: u.add(m.group(2))
    return {x for x in d if x in CS},{x for x in u if x in CS}
I=[]  # flat instruction list: (block idx, text)
for k,b in enumerate(blocks):
    for s in b['ins']: I.append((k,s))
start={};end={};p=0
for k,b in enumerate(blocks): start[k]=p; p+=len(b['ins']); end[k]=p
def succ_ins(n):
    k,_=I[n]
    if n+1<end[k]: return [n+1]
    return [start[bid[s]] for s in blocks[k]['succ'] if s in bid and start[bid[s]]<end[bid[s]]]
S=[succ_ins(n) for n in range(len(I))]
PR=collections.defaultdict(list)
for n,ss in enumerate(S):
    for m in ss: PR[m].append(n)
DU=[du(s) for _,s in I]
# liveness (backward)
LIN=[set() for _ in I]; LOUT=[set() for _ in I]
work=collections.deque(range(len(I)-1,-1,-1)); inq=set(work)
while work:
    n=work.popleft(); inq.discard(n)
    o=set().union(*[LIN[m] for m in S[n]]) if S[n] else set()
    d,u=DU[n]; i_=(o-d)|u
    LOUT[n]=o
    if i_!=LIN[n]:
        LIN[n]=i_
        for m in PR[n]:
            if m not in inq: work.append(m); inq.add(m)
# reaching defs (forward)
RIN=[dict() for _ in I]; ROUT=[dict() for _ in I]
work=collections.deque(range(len(I))); inq=set(work)
while work:
    n=work.popleft(); inq.discard(n)
    m={}
    for p in PR[n]:
        for r,v in ROUT[p].items(): m[r]=m.get(r,frozenset())|v
    RIN[n]=m; o=dict(m)
    for r in DU[n][0]: o[r]=frozenset([n])
    if o!=ROUT[n]:
        ROUT[n]=o
        for q in S[n]:
            if q not in inq: work.append(q); inq.add(q)
def find(pat,which=0):
    hits=[n for n,(k,s) in enumerate(I) if s.startswith('JAL') and re.search(pat,s)]
    return hits[which] if hits and len(hits)>abs(which if which>=0 else which+1) else None
pts={}
pts['w_ata']=find('create_idempotent')
pts['collect']=find('collect_creator_fee')
pts['w_frz']=find('token_frozen')
fpa=[n for n,(k,s) in enumerate(I) if s.startswith('JAL') and 'find_program_address' in s]
pts['sweep']=fpa[1] if len(fpa)>1 else None
pts['tcf']=find('transfer_creator_fees_to_pump_v2')
pts['shcpi']=find('admin_cto_sharing_config')
pool=find('admin_cto_pool'); pts['pool']=pool
if pool is not None:
    die=[n for n,(k,s) in enumerate(I) if s.startswith('JAL') and 'data_is_empty' in s and n<pool]
    pts['poolgate']=die[-1] if die else None
pbc=[n for n,(k,x) in enumerate(I) if x.startswith('JAL') and 'prepare_bonding_curve' in x]
SW=pbc[0] if pbc else (pts['sweep'] or 0)
res={}
for nm in ('w_frz','w_ata','collect','sweep','tcf','shcpi','poolgate','pool'):
    n=pts.get(nm)
    if n is None: continue
    live=sorted(LIN[n]&set(CS)); row={}
    for r in live:
        ds=sorted(RIN[n].get(r,()))
        row[r]=[('head' if d<SW else 'tail')+f'@{d} bb.{blocks[I[d][0]]["id"]}: '+I[d][1][:90] for d in ds[:4]]+([f'... {len(ds)} defs'] if len(ds)>4 else [])
    res[nm]={'at':f'{n} bb.{blocks[I[n][0]]["id"]}','live':live,'defs':row}
if '--json' in sys.argv: print(json.dumps(res))
else:
    for nm,r in res.items():
        print(f'== {nm} ({r["at"]}): live callee-saved {r["live"]}')
        for reg,ds in r['defs'].items():
            for d in ds: print(f'   {reg} <- {d}')
