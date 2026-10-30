#!/usr/bin/env python3
"""frsweep.py <m.ll> OUT.jsonl [-j N] [--base SPEC]: alloca-level frame oracle on a slim post-opt module.
Items per alloca A: mv:A:FIRST, mv:A:END, nolt:A. Scores like bwfm (plain ratio, fm, sk)."""
import sys,os,re,json,subprocess,tempfile
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import bwx,bwfm
from concurrent.futures import ThreadPoolExecutor
def fn_span(t):
    m=re.search(r'^define [^\n]*@_ZN14pump_recovered9admin_cto7execute[^\n]*\{\n',t,re.M); i=m.start(); j=t.index('\n}\n',i)+3; return i,j
def apply(t,spec):
    for it in [x for x in spec.split(',') if x]:
        p=it.split(':'); i,j=fn_span(t); f=t[i:j]
        if p[0] in ('bw','inv','strip'): t=bwx.apply(t,it); continue
        if p[0]=='mv':
            L=f.split('\n'); ia=next(k for k,l in enumerate(L) if re.match(r'\s*%'+re.escape(p[1])+r' = alloca ',l)); la=L.pop(ia)
            al=[k for k,l in enumerate(L) if re.match(r'\s*%\S+ = alloca ',l)]
            ib=al[-1]+1 if p[2]=='END' else (al[0] if p[2]=='FIRST' else next(k for k,l in enumerate(L) if re.match(r'\s*%'+re.escape(p[2])+r' = alloca ',l)))
            L.insert(ib,la); f='\n'.join(L)
        elif p[0]=='nolt':
            f,n=re.subn(r'\n\s*call void @llvm\.lifetime\.(?:start|end)\.p0\(i64 \d+, ptr (?:nonnull )?%'+re.escape(p[1])+r'\)[^\n]*','',f)
        elif p[0]=='sz':
            f,n=re.subn(r'(%'+re.escape(p[1])+r' = alloca )\[\d+ x i8\]',r'\g<1>['+p[2]+' x i8]',f)
        t=t[:i]+f+t[j:]
    return t
def run(mod,spec,ot,keep=None):
    with tempfile.TemporaryDirectory(dir=bwfm.OUT) as d:
        open(d+'/m.ll','w').write(apply(mod,spec))
        r=subprocess.run([bwx.LLC,*bwx.F,d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
        if r.returncode: return {'spec':spec,'error':r.stderr[-200:]}
        res={'spec':spec,**bwfm.score(d+'/m.o',ot)}
        if keep: os.makedirs(keep,exist_ok=True); os.replace(d+'/m.o',keep+'/m.o'); os.replace(d+'/m.ll',keep+'/m.ll')
        return res
if __name__=='__main__':
    a=sys.argv[1:]; cmd=a.pop(0); mod=open(a.pop(0)).read(); ot=bwx.orig_toks()
    if cmd=='run':
        keep=a[a.index('--keep')+1] if '--keep' in a else None
        print(json.dumps(run(mod,a[0] if a and not a[0].startswith('--') else '',ot,keep))); sys.exit()
    outp=a.pop(0); j=int(a[a.index('-j')+1]) if '-j' in a else 4; base=a[a.index('--base')+1] if '--base' in a else ''
    i,k=fn_span(mod); als=re.findall(r'^\s*%(\S+) = alloca ',mod[i:k],re.M)
    ops=a[a.index('--ops')+1].split(',') if '--ops' in a else ['mvF','mvE','nolt']
    items=[]
    for x in als:
        if 'mvF' in ops: items.append(f'mv:{x}:FIRST')
        if 'mvE' in ops: items.append(f'mv:{x}:END')
        if 'nolt' in ops and re.search(r'lifetime\.start\.p0\(i64 \d+, ptr (nonnull )?%'+re.escape(x)+r'\)',mod[i:k]): items.append(f'nolt:{x}')
    f=open(outp,'a')
    def go(it):
        r=run(mod,(base+',' if base else '')+it,ot); r['item']=it; f.write(json.dumps(r)+'\n'); f.flush(); return r
    with ThreadPoolExecutor(j) as ex: list(ex.map(go,items))
