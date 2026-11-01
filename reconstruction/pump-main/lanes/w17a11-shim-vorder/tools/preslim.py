#!/usr/bin/env python3
"""preslim.py <in.ll> <out.ll> [mode]: reduce a PRE-OPT module to execute's reference closure (experiment only).
Non-closure defines become declarations, non-closure globals are dropped, unreachable metadata is pruned.
mode 'keep' (default) adds an optnone caller that keeps every closure function with outside callers multi-use."""
import sys,os,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import modparse
ROOT=r'admin_cto7execute|admin_cto8validate'
def to_decl(first):
    d=first[len('define '):].rstrip(); assert d.endswith('{'); d=d[:-1].rstrip()
    for _ in range(3): d=re.sub(r'^(internal|private|linkonce_odr|weak_odr|dso_local|unnamed_addr|hidden)\s+','',d)
    d=re.sub(r'\s+comdat(\([^)]*\))?','',d); d=re.sub(r'\s+personality\s+ptr\s+@\S+','',d)
    d=re.sub(r'\s+!dbg !\d+','',d); d=re.sub(r'\s+prefix\s+\S+','',d)
    d=re.sub(r' (%[\w.$"-]+)(?=[,)])','',d)
    return 'declare '+d
def split_params(s):
    out=[];depth=0;cur=''
    for ch in s:
        if ch in '([{<': depth+=1
        elif ch in ')]}>': depth-=1
        if ch==',' and depth==0: out.append(cur.strip()); cur=''
        else: cur+=ch
    if cur.strip(): out.append(cur.strip())
    return out
def ptype(p):
    # leading type of a parameter: handles {..}, [..], <..>, ptr, iN
    p=p.strip()
    if p[0] in '{[<':
        close={'{':'}','[':']','<':'>'}[p[0]]; depth=0
        for i,ch in enumerate(p):
            if ch==p[0]: depth+=1
            elif ch==close:
                depth-=1
                if depth==0: return p[:i+1]
    return p.split()[0]
def main(inp,outp,mode='keep'):
    t=open(inp).read(); E=modparse.parse(t)
    defs={n:l for k,n,l in E if k=='define'}; globs={n:l for k,n,l in E if k=='global'}
    roots=[n for n in defs if re.search(ROOT,n)]
    K=set(); st=list(roots)
    while st:
        x=st.pop()
        if x in K: continue
        K.add(x)
        if x in defs: st.extend(r for r in modparse.refs(defs[x][1:]) if r in defs or r in globs)
        elif x in globs: st.extend(r for r in modparse.refs(globs[x]) if r!=x and (r in defs or r in globs))
    # outside users of closure functions
    outside=set()
    if mode=='keep':
        for k,n,l in E:
            if k=='define' and n not in K:
                for r in modparse.refs(l[1:]):
                    if r in K and r in defs: outside.add(r)
            elif k=='global' and n not in K:
                for r in modparse.refs(l):
                    if r in K and r in defs: outside.add(r)
    out=[]; declared=set()
    for k,n,l in E:
        if k=='define':
            if n in K: out.extend(l)
            else: out.append(to_decl(l[0])); declared.add(n)
        elif k=='global':
            if n in K or n.startswith('@llvm.'): 
                if n.startswith('@llvm.used') or n.startswith('@llvm.compiler.used'): continue
                out.extend(l)
        elif k=='declare': out.extend(l)
        elif k=='meta': out.extend(l)
        else:
            if l[0].startswith('@') and ' alias ' in l[0]: continue
            out.extend(l)
    import collections
    callargs=collections.defaultdict(lambda: collections.defaultdict(set))
    def scan_calls(lines):
        for l in lines:
            if 'call' not in l: continue
            for f in re.findall(r'(@"[^"]+"|@[\w.$-]+)\(',l):
                if f not in outside: continue
                s2=l[l.index(f+'(')+len(f)+1:]; d=1; k=0
                while d and k<len(s2):
                    if s2[k] in '([{': d+=1
                    elif s2[k] in ')]}': d-=1
                    k+=1
                for pi,a in enumerate(split_params(s2[:k-1])):
                    v=a.split()[-1] if a.split() else a
                    callargs[f][pi].add(v)
    for k_,n_,l_ in E:
        if k_=='define': scan_calls(l_[1:])
    def const_args(f):
        out={}
        for pi,vs in callargs[f].items():
            if len(vs)==1:
                v=next(iter(vs))
                if re.match(r'^(-?\d+|true|false|null|poison|undef|@[\w.$"-]+)$',v): out[pi]=v
        return out
    if outside:
        body=['define void @__keep_uses() #%s {'%'KEEPATTR','start:']; i=0
        surv=set(open(os.environ['SURV']).read().split('\n')) if os.environ.get('SURV') else None
        for f in sorted(outside):
            if surv is not None and f not in surv: continue
            hdr=defs[f][0]
            if 'internal' not in hdr.split('@')[0] and 'private' not in hdr.split('@')[0]: continue
            m=re.match(r'define (.*?)(@"[^"]+"|@[\w.$-]+)\((.*)\)(.*)\{$',hdr)
            pre,args=m.group(1),m.group(3)
            # args may contain ')' in attributes: find matching paren
            s=hdr[hdr.index(f)+len(f):]; depth=0
            for j,ch in enumerate(s):
                if ch=='(': depth+=1
                elif ch==')':
                    depth-=1
                    if depth==0: args=s[1:j]; break
            toks=pre.split(); cc=[x for x in toks if x in('fastcc','coldcc','ccc')]
            ret=[x for x in toks if x not in('internal','private','dso_local','unnamed_addr','fastcc','coldcc','ccc','hidden','noundef','zeroext','signext','noalias','nonnull') and not x.startswith('align') and not x.startswith('dereferenceable') and not x.startswith('range(')]
            rty=ret[-1] if ret else 'void'
            if pre.count('{'):  # struct return
                rty=pre[pre.index('{'):pre.rindex('}')+1]
            vals=[]
            cst=const_args(f)
            for pi,p in enumerate(split_params(args)):
                if p=='...': continue
                ty=ptype(p)
                if cst.get(pi) is not None: vals.append((ty,cst[pi])); continue
                vals.append((ty,'%%v%d'%i)); body.append('  %%v%d = load volatile %s, ptr @__opaque'%(i,ty)); i+=1
            call='  call %s%s %s(%s)'%(cc[0]+' ' if cc else '',rty,f,', '.join('%s %s'%(a,b) for a,b in vals))
            body.append(call)
        body+=['  ret void','}']
        out.insert(0,'')
        out.append('@__opaque = external global [64 x i8]')
        out.extend(body)
        out.append('attributes #KEEPATTR = { noinline optnone }')
    txt='\n'.join(out)
    # prune metadata not reachable
    lines=txt.split('\n'); md={}; rest=[]
    for l in lines:
        m=re.match(r'^!(\d+) = ',l)
        if m: md[m.group(1)]=l
        else: rest.append(l)
    body='\n'.join(rest); seen=set(); stck=re.findall(r'!(\d+)\b',body)
    while stck:
        x=stck.pop()
        if x in seen or x not in md: continue
        seen.add(x); stck.extend(re.findall(r'!(\d+)\b',md[x][len(x)+1:]))
    txt='\n'.join(rest+[md[x] for x in sorted(seen,key=int)])+'\n'
    txt=txt.replace('#KEEPATTR','#9999')
    open(outp,'w').write(txt)
    return len(K),len(outside)
if __name__=='__main__':
    print(main(*sys.argv[1:]))
