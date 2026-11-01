#!/usr/bin/env python3
"""bscreen.py <base m.ll> <kind> <outfile> [workers] [lo hi]: single-edit IR screen (experiment only).
kind: load (make one load volatile), store (one store volatile), memcpy (one memcpy volatile).
For each candidate line of execute: llc (SDK), M, region dM vs main, and the TCF orig-r8 / wallet orig-r9 register maps.
Prints rows whose TCF or wallet differs from the base's register basin, or whose M beats the base."""
import sys,os,re,subprocess,json,tempfile,difflib
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,regprof,xled,numpy as np
from regs import R
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
a=sys.argv[1:]; base,kind,outf=a[0],a[1],a[2]; W=int(a[3]) if len(a)>3 else 4
L=open(base).read().split('\n')
s=[i for i,l in enumerate(L) if l.startswith('define ') and 'admin_cto7execute' in l][0]
e=s+next(i for i,l in enumerate(L[s:]) if l=='}')
lo,hi=(int(a[4]),int(a[5])) if len(a)>5 else (s+1,e+1)
O=oracle.orig_window(); ot,oo=xled.toks(O); OF=xled.fmask(ot); OO=np.array(regprof.OO)
HR=regprof.hits('main')[0]
def edit(i):
    l=L[i]
    if kind=='load':
        m=re.match(r'^(\s*%[\w.$"]+ = )load (?!volatile)(.*)$',l)
        return m.group(1)+'load volatile '+m.group(2) if m else None
    if kind=='memcpy':
        if 'call void @llvm.memcpy' not in l or not l.rstrip().endswith('i1 false)'): return None
        return l.rstrip()[:-len('i1 false)')]+'i1 true)'
    if kind=='store':
        m=re.match(r'^(\s*)store (?!volatile)(.*)$',l)
        return m.group(1)+'store volatile '+m.group(2) if m else None
    if kind.startswith('bw'):
        # bw:<a>:<b> -> branch_weights a:b on one conditional br (replacing any existing !prof)
        if not re.match(r'^\s*br i1 %',l): return None
        _,wa,wb=kind.split(':')
        l2=re.sub(r', !prof !\d+','',l)
        return l2+', !prof !99990'
def rmap(c,lo,hi,r):
    ct,co=xled.toks(c); m=Counter()
    for bl in difflib.SequenceMatcher(None,OF,xled.fmask(ct),autojunk=False).get_matching_blocks():
        for k in range(bl.size):
            i=bl.a+k; j=bl.b+k
            if not (lo<=oo[i]<hi): continue
            for sh in (0,4):
                p=(ot[i][1]>>sh)&15; q=(ct[j][1]>>sh)&15
                if p==r: m[q]+=1
    return ' '.join(f'r{b}:{n}' for b,n in m.most_common(2))
def score(c):
    ct,_=xled.toks(c); h=np.zeros(len(ot),bool)
    for bl in difflib.SequenceMatcher(None,ot,ct,autojunk=False).get_matching_blocks(): h[bl.a:bl.a+bl.size]=True
    dr={}
    for lo_,hi_,n in R:
        mm=(OO>=lo_)&(OO<hi_); x=int(h[mm].sum()-HR[mm].sum())
        if x: dr[n]=x
    return int(h.sum()),dr
def run(i):
    T2=L[:]; T2[i]=edit(i)
    if kind.startswith('bw'):
        _,wa,wb=kind.split(':'); T2.append(f'!99990 = !{{!"branch_weights", i32 {wa}, i32 {wb}}}')
    d=tempfile.mkdtemp(prefix='bs',dir=os.path.dirname(outf))
    p=d+'/m.ll'; open(p,'w').write('\n'.join(T2))
    r=subprocess.run(['nice','-n','5',SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',p,'-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: res={'line':i+1,'err':r.stderr[-200:]}
    else:
        c=oracle.elf_fn(d+'/m.o',oracle.KEEP); M,dr=score(c)
        res={'line':i+1,'bytes':len(c),'M':M,'dreg':dr,'tcf_r8':rmap(c,0x2600,0x3c00,8),'w_r9':rmap(c,0x5a00,0x6c00,9),'src':L[i].strip()[:120]}
    subprocess.run(['rm','-rf',d])
    with open(outf,'a') as f: f.write(json.dumps(res)+'\n')
    return res
idx=[i for i in range(lo-1,hi-1) if edit(i)]
print(len(idx),'candidates',flush=True)
with ThreadPoolExecutor(W) as ex: list(ex.map(run,idx))
