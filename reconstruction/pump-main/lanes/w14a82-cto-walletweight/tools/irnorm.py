#!/usr/bin/env python3
"""irnorm.py <a.ll> <b.ll>: diff execute's body with local value/block names canonicalised by first occurrence."""
import sys,re,difflib
def body(p):
    t=open(p).read(); i=t.index('\ndefine'); i=t.index('admin_cto7execute17',i); i=t.rindex('\ndefine',0,i); j=t.index('\n}\n',i)
    L=t[i:j].split('\n'); m={}; out=[]
    tok=re.compile(r'%("[^"]+"|[-\w.$]+)')
    for l in L:
        def f(x):
            k=x.group(0)
            if k not in m: m[k]='%%v%d'%len(m)
            return m[k]
        l=re.sub(r'!\d+','!M',l); out.append(tok.sub(f,l))
    return out
a=body(sys.argv[1]); b=body(sys.argv[2])
for l in difflib.unified_diff(a,b,lineterm='',n=1): print(l[:200])
