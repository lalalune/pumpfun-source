#!/usr/bin/env python3
"""addlt.py <m.ll> [names...]: oracle adding lifetime markers to execute allocas that lack them.
Modes per alloca A: addlt:A (start before first use, end after last use, textual order), addlt0:A (start after the allocas)."""
import sys,re,json,os,tempfile,subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import frsweep,bwx,bwfm
def addlt(t,a,mode):
    i,j=frsweep.fn_span(t); L=t[i:j].split('\n')
    k=next(n for n,l in enumerate(L) if re.match(r'\s*%'+re.escape(a)+r' = alloca \[(\d+) x i8\]',l))
    sz=re.search(r'\[(\d+) x i8\]',L[k]).group(1)
    us=[n for n,l in enumerate(L) if n!=k and re.search(r'%'+re.escape(a)+r'\b',l)]
    s=f'  call void @llvm.lifetime.start.p0(i64 {sz}, ptr nonnull %{a})'; e=f'  call void @llvm.lifetime.end.p0(i64 {sz}, ptr nonnull %{a})'
    last=us[-1]
    if mode=='addlt0':
        al=[n for n,l in enumerate(L) if re.match(r'\s*%\S+ = alloca ',l)]; first=al[-1]+1
    else:
        first=us[0]
        # do not split a phi group or put before a GEP def used by the first use: place before first use line
    L.insert(last+1,e); L.insert(first,s)
    return t[:i]+'\n'.join(L)+t[j:]
if __name__=='__main__':
    mod=open(sys.argv[1]).read(); ot=bwx.orig_toks(); names=sys.argv[2:]
    i,j=frsweep.fn_span(mod); f=mod[i:j]
    if not names:
        names=[a for a in re.findall(r'^\s*%(\S+) = alloca ',f,re.M) if not re.search(r'lifetime\.start\.p0\(i64 \d+, ptr (nonnull )?%'+re.escape(a)+r'\)',f)]
    for a in names:
        for mode in ('addlt','addlt0'):
            with tempfile.TemporaryDirectory(dir=bwfm.OUT) as d:
                open(d+'/m.ll','w').write(addlt(mod,a,mode))
                r=subprocess.run([bwx.LLC,*bwx.F,d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
                if r.returncode: print(json.dumps({'item':f'{mode}:{a}','error':r.stderr[-200:]})); continue
                print(json.dumps({'item':f'{mode}:{a}',**bwfm.score(d+'/m.o',ot)}),flush=True)
