#!/usr/bin/env python3
"""hprobe.py <base m.ll (capopt post-opt)> <specs.py> <out.jsonl> [--par N] [--ref frame.txt] [--keep]
Post-opt (llc-only) frame stand-in screen for admin_cto::execute (w17a30-shim-hk2stand). Experiment only.
A spec is (name, dict) with keys:
  alloc: (anchor_regex_of_alloca_line, '<'|'>', size, align)   -> inserts  %X = alloca [size x i8], align a
  ops:   list of (kind, anchor_regex, nth, side)  kind in S (lifetime.start X), E (lifetime.end X), V (var.annotation X),
         or ('RAW', anchor_regex, nth, side, text) to insert a raw line, or ('D', anchor_regex, nth) to delete a line.
  name:  IR name of the stand-in (default hk2s)
side '<' inserts before the anchor line, '>' after it (after a label line, it skips the block's phi lines).
Scores M (exact matched tokens, fx.Mof), bytes, sig, frame map diff vs ref (nfd), and where skm / the validate
error-name Strings / the stand-in land."""
import sys,os,re,json,subprocess,runpy,hashlib,difflib
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.dirname(T); sys.path.insert(0,T)
import fx,oracle
NAMES=os.environ.get('NAMES','_95.i _49.i _37.i _27.i _15.i buf.i41.i buf.i34.i').split()
DECL='declare void @llvm.var.annotation.p0.p0(ptr, ptr, ptr, i32, ptr)'
def span(t):
    m=re.search(r'^define[^\n]*admin_cto7execute17h.*?^}',t,re.M|re.S); return m.start(),m.end()
def find(body,anc,nth):
    idx=[k for k,l in enumerate(body) if re.search(anc,l)]
    if not idx: raise ValueError('no anchor '+anc)
    return idx[nth]
def apply(t,spec):
    X=spec.get('name','hk2s')
    i,j=span(t); body=t[i:j].split('\n')
    if 'alloc' in spec:
        anc,side,sz,al=spec['alloc']; k=find(body,anc,0)
        body.insert(k if side=='<' else k+1,f'  %{X} = alloca [{sz} x i8], align {al}')
        size=sz
    else:
        size=spec.get('size',32)
    for op in spec.get('ops',[]):
        kind=op[0]
        if kind=='D':
            k=find(body,op[1],op[2]); del body[k]; continue
        anc,nth,side=op[1],op[2],op[3]
        k=find(body,anc,nth)
        if side=='>':
            k+=1
            if re.match(r'^[\w.$"\-]+:',body[k-1]):
                while k<len(body) and re.match(r'^\s+%\S+ = phi ',body[k]): k+=1
        if kind=='S': line=f'  call void @llvm.lifetime.start.p0(i64 {size}, ptr nonnull %{X})'
        elif kind=='E': line=f'  call void @llvm.lifetime.end.p0(i64 {size}, ptr nonnull %{X})'
        elif kind=='V': line=f'  call void @llvm.var.annotation.p0.p0(ptr %{X}, ptr null, ptr null, i32 0, ptr null)'
        elif kind=='RAW': line=op[4]
        else: raise ValueError(kind)
        body.insert(k,line)
    t=t[:i]+'\n'.join(body)+t[j:]
    if 'llvm.var.annotation' in t and DECL not in t: t=t+'\n'+DECL+'\n'
    if spec.get('order'): t=reorder(t,spec['order'])
    if spec.get('w'): t=weights(t,spec['w'])
    return t
TSN='_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h1551814bef63e52cE'
def reorder(t,order):
    import mv11 as mv
    t=mv.denum(t)
    L,st,en,S=mv.blocks(t)
    B=[(s,(S[k+1] if k+1<len(S) else en)) for k,s in enumerate(S)]
    names=[mv.name_of(L[s]) for s,_ in B]
    want=[x.replace('TS.',TSN+'.') for x in order.split()]
    for w in want: assert w in names,w
    idx={n:i for i,n in enumerate(names)}
    first=min(idx[w] for w in want)
    seq=[i for i in range(len(B)) if names[i] not in want]
    pos=sum(1 for i in seq if i<first)
    seq=seq[:pos]+[idx[w] for w in want]+seq[pos:]
    body=[]
    for i in seq: body+=L[B[i][0]:B[i][1]]
    return '\n'.join(L[:S[0]]+body+L[en:])
def weights(t,spec):
    L=t.split('\n')
    st=[i for i,l in enumerate(L) if l.startswith('define ') and re.search(oracle.KEEP,l)][0]
    en=st+[i for i,l in enumerate(L[st:]) if l=='}'][0]
    extra=[]; k=0
    for it in [x for x in spec.split(',') if x]:
        b,a,c=it.rsplit(':',2)
        bi=[i for i in range(st,en) if L[i].startswith(b+':') or L[i].startswith('"'+b+'":')]
        assert len(bi)==1,(b,bi)
        j=bi[0]+1
        while not (L[j].startswith('  br ') or L[j].startswith('  switch ')): j+=1
        L[j]=re.sub(r', !prof !\d+','',L[j]); k+=1; L[j]=L[j]+', !prof !88880%d'%k
        extra.append('!88880%d = !{!"branch_weights", i32 %s, i32 %s}'%(k,a,c))
    return '\n'.join(L)+'\n'+'\n'.join(extra)+'\n'
def where(fr,nm):
    for l in fr.split('\n'):
        toks=l.split()
        if len(toks)<4: continue
        mem=[toks[3]]+[re.sub(r'\(\d+\)$','',x) for x in toks[4:]]
        if nm in mem: return toks[0]
    return None
def run(text,name,ref,keep=False):
    d=f'{OUT}/hp/{name}'; os.makedirs(d,exist_ok=True)
    open(d+'/m.ll','w').write(text)
    r=subprocess.run(['nice','-n','5',fx.LLC,*fx.LLCA,d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: return {'name':name,'err':'llc:'+r.stderr[-300:]}
    b=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(b); os.remove(d+'/m.o')
    M,ratio=fx.Mof(b)
    fr=subprocess.run(['python3',T+'/framemap.py',d+'/m.ll'],capture_output=True,text=True).stdout
    open(d+'/frame.txt','w').write(fr)
    if not keep: os.remove(d+'/m.ll')
    m0=[l[:6]+l[12:18] for l in open(ref).read().split('\n')]; f1=[l[:6]+l[12:18] for l in fr.split('\n')]
    dd=[l for l in difflib.unified_diff(m0,f1,lineterm='',n=0) if l[:1] in '+-' and l[:3] not in ('+++','---')]
    nw={n:where(fr,n) for n in NAMES}
    return {'name':name,'M':M,'ratio':round(ratio,5),'bytes':len(b),'sig':hashlib.sha1(b''.join(oracle.mask(b))).hexdigest()[:12],
            'nfd':len(dd),'skm':where(fr,'skm'),'X':where(fr,'hk2s'),'names':sorted(set(v or '-' for v in nw.values())),'fdiff':' | '.join(dd)[:300]}
if __name__=='__main__':
    a=sys.argv[1:]; base=open(a[0]).read(); S=runpy.run_path(a[1])['SPECS']; outp=a[2]
    par=int(a[a.index('--par')+1]) if '--par' in a else 4
    ref=a[a.index('--ref')+1] if '--ref' in a else OUT+'/ir/frame_m0.txt'
    keep='--keep' in a
    def one(s):
        try: t=apply(base,s[1])
        except Exception as e: return {'name':s[0],'err':str(e)[:200]}
        return run(t,s[0],ref,keep)
    with ThreadPoolExecutor(par) as ex:
        for r in ex.map(one,S):
            print(json.dumps(r),flush=True); open(outp,'a').write(json.dumps(r)+'\n')
