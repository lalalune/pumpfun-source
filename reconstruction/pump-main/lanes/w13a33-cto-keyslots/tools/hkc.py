#!/usr/bin/env python3
"""hkc.py <m.ll> SPEC...  post-opt llc oracle: holder_key copy (hkc) + px specs.
SPEC items (comma list): hkc[:POS] (add copy; POS=alloca name to insert before, or END/TOP), arm (holder arm reads hkc),
cmp (validate memcmp reads hkc), plus px items mv:A:B / nolt:A."""
import sys,os,re,json
sys.path.insert(0,os.path.dirname(__file__))
import px
def fn_lines(t):
    s,e=px.fnbounds(t); return s,e,t[s:e].split('\n')
def hkc(t,pos,arm,cmp,lt='sk'):
    s,e,L=fn_lines(t)
    al=[i for i,l in enumerate(L) if ' = alloca ' in l]
    line='  %hkc = alloca [32 x i8], align 1'
    if pos=='END': b=al[-1]+1
    elif pos=='TOP': b=al[0]
    else: b=[i for i,l in enumerate(L) if l.strip().startswith('%'+pos+' = alloca ')][0]
    L.insert(b,line)
    i=[i for i,l in enumerate(L) if 'memcpy' in l and '%sk, ptr' in l][0]
    L[i+1:i+1]=['  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %hkc)',
                '  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(32) %hkc, ptr noundef nonnull align 1 dereferenceable(32) %holder_key, i64 32, i1 false)']
    for i,l in enumerate(L):
        if 'llvm.lifetime.end' in l and '(i64 32, ptr nonnull %'+lt+')' in l:
            L[i]=l+'\n  call void @llvm.lifetime.end.p0(i64 32, ptr nonnull %hkc)'
        if cmp and '@memcmp' in l and '%t.i,' in l and '%holder_key,' in l:
            L[i]=l.replace('%holder_key,','%hkc,')
        if arm and 'target.i.sroa' in l and ('%holder_key,' in l or '%hk, i64 7' in l):
            L[i]=l.replace('%holder_key,','%hkc,').replace('%hk, i64 7','%hkc, i64 7')
    return t[:s]+'\n'.join(L)+t[e:]
def apply(t,spec):
    rest=[]
    for it in spec.split(','):
        k=it.split(':')
        if k[0]=='hkc':
            pos=k[1] if len(k)>1 else 'END'; f=set(spec.split(','))
            t=hkc(t,pos,'arm' in f,'cmp' in f,k[2] if len(k)>2 else 'sk')
        elif k[0] in ('arm','cmp',''): pass
        else: rest.append(it)
    return px.apply(t,','.join(rest))
px_apply_orig=px.apply
if __name__=='__main__':
    base=sys.argv[1]; specs=sys.argv[2:]
    a=px.apply
    def ap(t,spec): 
        px.apply=a
        r=apply(t,spec); return r
    import types
    def run(i,sp):
        d=px.OUT+'/px/hk%d_%d'%(os.getpid(),i); os.makedirs(d,exist_ok=True)
        t=apply(open(base).read(),sp); open(d+'/m.ll','w').write(t)
        import subprocess
        r=subprocess.run([px.SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
        if r.returncode: return {'spec':sp,'err':r.stderr[-500:]}
        if px.ORIG is None: px.ORIG=px.orig_window()
        cand=px.elf_fn(d+'/m.o',px.KEEP); rr,sd=px.metric(cand,px.ORIG)
        if os.environ.get('RM'): __import__('shutil').rmtree(d)
        return {'spec':sp,'ratio':round(rr,5),'bytes':len(cand),'slots_diff':sd}
    px.ORIG=px.orig_window()
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(4) as ex:
        for r in ex.map(lambda x: run(*x), enumerate(specs)): print(json.dumps(r),flush=True)
