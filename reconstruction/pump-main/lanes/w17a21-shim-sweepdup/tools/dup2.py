#!/usr/bin/env python3
"""dup2.py: copy the post-sweep Result test into sweep exit predecessors (post-opt IR edit, experiment only).
dup(t, site, ne=False, w=None): site is a pred of bb57.i119 or bb60.i108 (ending in an unconditional br)."""
import re,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import irf
SX='_ZN14pump_recovered9admin_cto7execute5sweep17h9943ff4781c7e018E.exit'
J57='bb57.i119'; J60='bb60.i109'; OK='bb93'; EJ='bb70'
def setnames(t):
    global J57,J60,S660,S648,SRENT
    i,j,h,B,order=irf.parse(t)
    P=irf.preds(B)
    sx=[p for p in P[SX]]
    def has(b,pat): return any(pat in l for l in B[b])
    J60=max(sx,key=lambda p:len(P[p]))
    c=[p for p in P[J60] if has(p,'with_pubkeys')]; assert len(c)==1,c; S648=c[0]
    c=[p for p in P[J60] if has(p,'store i32 660,')]; assert len(c)==1,c; S660=c[0]
    c=[p for p in P[J60] if len(P[p])>=4 and all(('phi' in l or 'lifetime.end' in l or l.strip().startswith('br ') or l.endswith(':') or '; preds' in l) for l in B[p] if l.strip())]
    J57=c[0] if c else None
    r=[p for p in (P[J57] if J57 else []) if has(p,'ProgramError$GT$$GT$4from')]
    SRENT=r[0] if r else None
    return dict(J57=J57,J60=J60,S660=S660,S648=S648,SRENT=SRENT)
def lt_of(blk):
    return [l for l in blk if 'llvm.lifetime.end' in l]
def phis(blk):
    out=[]
    for l in blk:
        m=re.match(r'\s+(%[\w.$"-]+) = phi (\w+) (.*)$',l)
        if m: out.append((m.group(1),m.group(2),m.group(3),l))
    return out
def pick(rest,ref):
    for x in re.finditer(r'\[ ([^,\[\]]+), (%(?:"[^"]+"|[\w.$-]+)) \]',rest):
        if x.group(2)==ref: return x.group(1),x.group(0)
    raise KeyError(ref)
def drop_incoming(line,ref):
    v,e=pick(line,ref)
    if ', '+e in line: return line.replace(', '+e,'',1)
    return line.replace(e+', ','',1)
def add_incoming(line,val,ref):
    return line+', [ %s, %s ]'%(val,ref)
def edit_fn(t,f):
    i,j,h,B,order=irf.parse(t)
    B,order=f(B,order)
    body=h+'\n'+'\n'.join('\n'.join(B[n]) for n in order)+'\n}\n'
    # ensure blank lines between blocks
    body=re.sub(r'\n(?=("[^"]+"|[\w.$-]+):\s+; preds)', '\n\n', body)
    body=body.replace('\n\n\n','\n\n')
    return t[:i]+body+t[j:]
_k=[99900]
def dup(t,site,ne=False,w=None,place='after'):
    meta=''
    def f(B,order):
        S=site; ref='%'+S
        blk=B[S]
        tgt=irf.succs(blk); assert len(tgt)==1 and tgt[0] in (J57,J60),(S,tgt)
        chain=[J57,J60] if tgt[0]==J57 else [J60]
        # follow phis: value through chain
        cur_ref=ref; vals={}
        T=P=None
        # first join
        j0=B[chain[0]]; ph=phis(j0)
        assert len(ph)==2,ph
        T,_=pick(ph[0][2],ref); P,_=pick(ph[1][2],ref)
        # remove incoming from first join
        nb=[]
        for l in j0:
            if l in (ph[0][3],ph[1][3]): l=drop_incoming(l,ref)
            nb.append(l)
        B[chain[0]]=nb
        LT=[]
        for c in chain: LT+=lt_of(B[c])
        LT+=lt_of(B[SX])
        n=re.sub(r'[^\w]','_',S)[-40:]
        W=(', !prof !%d'%w) if w else ''
        lastbr=[k for k,l in enumerate(blk) if re.match(r'\s+br label %',l)]
        assert len(lastbr)==1
        k=lastbr[0]
        if ne: br=['  %%dupc.%s = icmp ne i64 %s, 2'%(n,T),'  br i1 %%dupc.%s, label %%dupE.%s, label %%%s%s'%(n,n,OK,W)]
        else: br=['  %%dupc.%s = icmp eq i64 %s, 2'%(n,T),'  br i1 %%dupc.%s, label %%%s, label %%dupE.%s%s'%(n,OK,n,W)]
        blk=blk[:k]+LT+br+blk[k+1:]
        B[S]=blk
        E='dupE.'+n
        B[E]=['%s:                                ; preds = %s'%(E,ref),'  %%dupp.%s = inttoptr i64 %s to ptr'%(n,P),'  br label %%%s'%EJ]
        pos=order.index(S)+1 if place=='after' else len(order)
        order.insert(pos,E)
        # OK phi
        ob=B[OK]; ph=phis(ob); assert len(ph)>=1
        B[OK]=[add_incoming(l,P,ref) if l==ph[0][3] else l for l in ob]
        # fix OK preds comment not needed
        eb=B[EJ]; ph=phis(eb)
        nb=[]
        for l in eb:
            if l==ph[0][3]: l=add_incoming(l,'%dupp.'+n,'%'+E)
            elif l==ph[1][3]: l=add_incoming(l,T,'%'+E)
            nb.append(l)
        B[EJ]=nb
        return B,order
    return edit_fn(t,f)
def W(t,a,b):
    _k[0]+=1; k=_k[0]
    return t+'\n!%d = !{!"branch_weights", i32 %d, i32 %d}\n'%(k,a,b), k
S648='"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h4b386cbefe3ebd9eE.exit.i"'
S660=None
SRENT='bb89.i'
def thread(t,site,place='end'):
    """route a known-Err pred of J60/J57 straight to the error exit EJ (what JumpThreading does in the original)."""
    def f(B,order):
        S=site; ref='%'+S; blk=B[S]
        tgt=irf.succs(blk); assert len(tgt)==1 and tgt[0] in (J57,J60),(S,tgt)
        chain=[J57,J60] if tgt[0]==J57 else [J60]
        j0=B[chain[0]]; ph=phis(j0); assert len(ph)==2
        T,_=pick(ph[0][2],ref); P,_=pick(ph[1][2],ref)
        B[chain[0]]=[drop_incoming(l,ref) if l in (ph[0][3],ph[1][3]) else l for l in j0]
        LT=[]
        for c in chain: LT+=lt_of(B[c])
        LT+=lt_of(B[SX])
        n=re.sub(r'[^\w]','_',S)[-40:]; E='thrE.'+n
        k=[i for i,l in enumerate(blk) if re.match(r'\s+br label %',l)][0]
        B[S]=blk[:k]+LT+['  br label %%%s'%E]+blk[k+1:]
        B[E]=['%s:                                ; preds = %s'%(E,ref),'  %%thrp.%s = inttoptr i64 %s to ptr'%(n,P),'  br label %%%s'%EJ]
        order.insert(order.index(S)+1 if place=='after' else len(order),E)
        eb=B[EJ]; ph=phis(eb); nb=[]
        for l in eb:
            if l==ph[0][3]: l=add_incoming(l,'%thrp.'+n,'%'+E)
            elif l==ph[1][3]: l=add_incoming(l,T,'%'+E)
            nb.append(l)
        B[EJ]=nb
        return B,order
    return edit_fn(t,f)
