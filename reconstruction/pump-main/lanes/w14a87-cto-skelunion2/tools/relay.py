#!/usr/bin/env python3
"""relay.py <m.s> <out.s> <spec>  (experiment only)
Branch-aware relayout oracle. Splits execute's asm into basic blocks (every label or '# %bb.N:' line), names each
block by its label (LBB0_n) or 'bb.N' for unlabeled ones (they get a real label), and makes every fallthrough explicit.
<spec> is a comma list of block names giving a NEW ORDER for a contiguous run of blocks: the run is the span from the
first to the last listed block in the original order; listed blocks are placed in spec order at the span's position,
unlisted blocks of the span keep their relative order after them unless spec contains '*' (then they go where '*' is).
Then fallthroughs are re-derived the BPF way (no condition reversal): a trailing 'ja X' whose X is the next block is
dropped; a block that fell through to S gets 'ja S' if S is no longer next. Prints ratio/bytes/slots and jm ratio."""
import sys,os,re,subprocess,tempfile,difflib
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx78.py').read(); G={}; exec(compile(src[:src.index("OUT=os.environ")],'rxhead','exec'),G)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
def parse(path):
    L=open(path).read().split('\n')
    fs=[k for k,l in enumerate(L) if re.match(r'^_ZN14pump_recovered9admin_cto7execute\w*:',l)][0]
    fe=[k for k,l in enumerate(L) if l.startswith('.Lfunc_end0')][0]
    st=[k for k in range(fs+1,fe) if re.match(r'^(LBB0_\d+:|# %bb\.\d+:)',L[k])]
    pre=L[:st[0]]; post=L[fe:]; blocks=[]
    for a,b in zip(st,st[1:]+[fe]):
        h=L[a]; m=re.match(r'^(LBB0_\d+):',h)
        if m: nm=m.group(1); body=L[a:b]
        else:
            n=re.match(r'^# %bb\.(\d+):(.*)$',h); nm='bb.'+n.group(1); body=['LBBX_%s:%s'%(n.group(1),n.group(2))]+L[a+1:b]
        blocks.append([nm,body])
    return pre,blocks,post
def lab(nm): return nm if nm.startswith('LBB0_') else 'LBBX_'+nm[3:]
def insns(body): return [i for i,l in enumerate(body) if l.strip() and not l.strip().startswith(('#','.')) and not re.match(r'^\S+:',l)]
def explicit(blocks):
    out=[]
    for k,(nm,body) in enumerate(blocks):
        body=list(body); ii=insns(body); last=body[ii[-1]].strip() if ii else ''
        ft = not (last.startswith('ja ') or last=='exit')
        out.append([nm,body,blocks[k+1][0] if ft and k+1<len(blocks) else None])
    return out
def emit(pre,eb,post):
    body=[]
    for k,(nm,b,ft) in enumerate(eb):
        b=list(b); nxt=eb[k+1][0] if k+1<len(eb) else None
        ii=insns(b)
        if ft is not None and ft!=nxt: b.append('\tja %s'%lab(ft))
        elif ft is None and ii:
            lastl=b[ii[-1]].strip()
            if nxt and lastl=='ja '+lab(nxt):
                # dropping is what BranchFolding does for an unconditional ja to the layout successor
                del b[ii[-1]]
        body+=b
    # retarget references to unlabeled blocks are already LBBX_ names only when we added them; old code never referenced bb.N
    return '\n'.join(pre+body+post)
def score(text):
    with tempfile.TemporaryDirectory() as d:
        s=d+'/a.s'; o=d+'/a.o'; open(s,'w').write(text)
        r=subprocess.run([SDK+'/clang','-cc1as','-triple','sbf','-target-feature','+store-imm','-target-feature','+jmp-ext','-filetype','obj',s,'-o',o],capture_output=True,text=True)
        if r.returncode: return {'err':r.stderr[-500:]}
        c=G['elf_fn'](o,G['KEEP'])
    O=G['orig_window']()
    def toks(raw,jm):
        out=[]
        for t in G['mask'](raw):
            t=bytearray(t); op=t[0]
            if jm and op&7==5 and op not in (0x85,0x95): t[2:4]=b'\0\0'
            out.append(bytes(t))
        return out
    rr,sd=G['metric'](c,O)
    jm=difflib.SequenceMatcher(None,toks(O,1),toks(c,1),autojunk=False).ratio()
    return {'ratio':round(rr,5),'bytes':len(c),'slots':sd,'jm':round(jm,5)}
def relayout(path,spec):
    pre,blocks,post=parse(path); eb=explicit(blocks); names=[x[0] for x in eb]
    for grp in spec.split(';'):
        if not grp: continue
        sp=grp.split(','); listed=[x for x in sp if x!='*']
        for x in listed: assert x in names,(x)
        idx=[names.index(x) for x in listed]; lo,hi=min(idx),max(idx)
        span=names[lo:hi+1]; rest=[x for x in span if x not in listed]
        if '*' in sp:
            new=[]
            for x in sp: new+= rest if x=='*' else [x]
        else: new=listed+rest
        m={x[0]:x for x in eb}
        eb=eb[:lo]+[m[x] for x in new]+eb[hi+1:]; names=[x[0] for x in eb]
    return emit(pre,eb,post)
if __name__=='__main__':
    p,o,spec=sys.argv[1:4]
    t=relayout(p,spec); open(o,'w').write(t)
    import json; print(json.dumps(score(t)))
