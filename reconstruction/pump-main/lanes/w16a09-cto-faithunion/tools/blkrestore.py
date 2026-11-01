#!/usr/bin/env python3
"""blkrestore.py <var.mir> <ref.mir> <out.mir> [fn-substring]: layout-restore oracle (experiment only).
Both MIRs are `llc -stop-after=block-placement` dumps. The variant's blocks of the execute function are stably re-sorted
into the reference layout: a block whose IR name (bb.N.<name>) occurs exactly once in both functions takes the reference
position of that name; every other block inherits the key of its layout predecessor (so unmatched runs travel with the
block before them). Fallthrough edges that the new order breaks get an explicit `JMP %bb.X`; an unconditional
`JMP %bb.X` to the new next block is dropped (as MBP would). Resume with `llc -start-after=block-placement`."""
import sys,re
from collections import Counter
HDR=re.compile(r'^  bb\.(\d+)(?:\.([^\s:(]+))?(.*):\s*$')
def split_fn(text,sub):
    # returns (prefix, fnbody_lines, suffix) for the machine function whose name contains sub
    i=0; parts=text.split('\n---\n')
    for k,p in enumerate(parts):
        if re.search(r'^name:\s+\S*'+re.escape(sub),p,re.M): return k,parts
    raise SystemExit('fn not found')
def blocks(body):
    lines=body.split('\n'); i=0
    while i<len(lines) and not HDR.match(lines[i]): i+=1
    head=lines[:i]; bl=[]; cur=None; tail=[]
    for l in lines[i:]:
        m=HDR.match(l)
        if m: cur={'n':int(m.group(1)),'name':m.group(2) or '','hdr':l,'lines':[]}; bl.append(cur); continue
        cur['lines'].append(l)
    # trailing non-block text (e.g. '...') stays with the last block; split it off
    last=bl[-1]['lines']; j=len(last)
    while j>0 and not last[j-1].startswith('    ') and not last[j-1].strip()=='' : j-=1
    return head,bl
BR=re.compile(r'^\s+(J[A-Za-z0-9_]+)\b.*%bb\.(\d+)\s*$')
def info(b):
    succ=[]; term=[]; uncond=None; noft=False
    for l in b['lines']:
        s=l.strip()
        if s.startswith('successors:'): succ=[int(x) for x in re.findall(r'%bb\.(\d+)',s)]
    ins=[l for l in b['lines'] if l.startswith('    ') and l.strip() and not l.strip().startswith(('successors:','liveins:',';'))]
    for l in ins:
        m=BR.match(l)
        if m:
            term.append(int(m.group(2)))
            if m.group(1)=='JMP': uncond=int(m.group(2))
    if ins and ins[-1].strip().split()[0] in ('EXIT','RET','JMP') : noft=True
    if ins and ins[-1].strip().startswith('JMP'): noft=True
    ft=None
    if not noft:
        rest=[x for x in succ if x not in term]
        if rest: ft=rest[0]
    return succ,term,uncond,ft
def main():
    vt=open(sys.argv[1]).read(); rt=open(sys.argv[2]).read(); out=sys.argv[3]; sub=sys.argv[4] if len(sys.argv)>4 else 'admin_cto7execute'
    kv,pv=split_fn(vt,sub); kr,pr=split_fn(rt,sub)
    fv=pv[kv]; m=re.search(r'\n\.\.\.\s*$',fv); tailv=fv[m.start():] if m else ''; fv=fv[:m.start()] if m else fv
    fr=pr[kr]; m2=re.search(r'\n\.\.\.\s*$',fr); fr=fr[:m2.start()] if m2 else fr
    hv,bv=blocks(fv); hr,br=blocks(fr)
    def sig(b):
        ks=[]
        for l in b['lines']:
            for m in re.finditer(r'@([\w$.]+)',l): ks.append(m.group(1)[-40:])
            m=re.search(r'(MOV_ri|STD_imm_V1|STW_imm|ST\w*imm\w*) (-?\d+)',l)
            if m and abs(int(m.group(2)))>=6000: ks.append(m.group(2))
        return tuple(ks) if ks else None
    cv=Counter(b['name'] for b in bv if b['name']); cr=Counter(b['name'] for b in br if b['name'])
    rpos={b['name']:i for i,b in enumerate(br) if b['name'] and cr[b['name']]==1}
    sv=Counter(sig(b) for b in bv); sr=Counter(sig(b) for b in br)
    spos={sig(b):i for i,b in enumerate(br) if sig(b) is not None and sr[sig(b)]==1}
    keys=[]; nm=0; ns=0
    for i,b in enumerate(bv):
        k=None
        if b['name'] and cv[b['name']]==1 and b['name'] in rpos: k=float(rpos[b['name']]); nm+=1
        else:
            g=sig(b)
            if g is not None and sv[g]==1 and g in spos: k=float(spos[g]); ns+=1
        keys.append(k)
    # segments: runs of the variant layout whose matched keys stay within W reference blocks of each other
    W=int(__import__('os').environ.get('BR_W','12')); segs=[]; cur=[]; last=None
    for i,k in enumerate(keys):
        if k is not None and last is not None and abs(k-last)>W and cur: segs.append(cur); cur=[]
        cur.append(i)
        if k is not None: last=k
    if cur: segs.append(cur)
    def skey(sg):
        ks=sorted(keys[i] for i in sg if keys[i] is not None)
        return ks[len(ks)//2] if ks else None
    sk=[]; prev=-1.0
    for sg in segs:
        k=skey(sg); k=prev+1e-3 if k is None else k; sk.append(k); prev=k
    if __import__('os').environ.get('BR_MODE','seg')=='blk':
        kk=[]; last=-1.0
        for k in keys:
            last=k if k is not None else last+1e-6; kk.append(last)
        order=sorted(range(len(bv)),key=lambda i:(kk[i],i))
    else:
        so=sorted(range(len(segs)),key=lambda j:(sk[j],j)); order=[i for j in so for i in segs[j]]
    nm=nm+ns
    nb=[bv[i] for i in order]
    added=dropped=0
    for j,b in enumerate(nb):
        succ,term,uncond,ft=info(b); nxt=nb[j+1]['n'] if j+1<len(nb) else None
        L=b['lines']
        # index of the last instruction line
        idx=max((q for q,l in enumerate(L) if l.startswith('    ') and l.strip() and not l.strip().startswith(('successors:','liveins:',';'))),default=None)
        if ft is not None and ft!=nxt:
            ins='    JMP %bb.'+str(ft)
            if idx is None: idx=max(q for q,l in enumerate(L) if l.strip().startswith(('successors:','liveins:')))
            L.insert(idx+1,ins); added+=1
        elif uncond is not None and uncond==nxt and idx is not None and L[idx].strip().startswith('JMP'):
            del L[idx]; dropped+=1
    body='\n'.join(hv+sum(([b['hdr']]+b['lines'] for b in nb),[]))
    pv[kv]=body+tailv
    open(out,'w').write('\n---\n'.join(pv))
    moved=sum(1 for a,b in zip(order,range(len(order))) if a!=b)
    print(f'blocks {len(bv)} matched {nm} moved {moved} jmp_added {added} jmp_dropped {dropped}',file=sys.stderr)
main()
