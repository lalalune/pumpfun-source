#!/usr/bin/env python3
"""addslot.py <in.ll> <out.ll> NAME:SIZE:BEFORE [...]: insert `%NAME = alloca [SIZE x i8]` before alloca %BEFORE in execute,
kept alive by one `store volatile i8 0` right after the alloca block (experiment only)."""
import sys,re
t=open(sys.argv[1]).read()
i=t.index('admin_cto7execute'); s=t.rfind('\ndefine',0,i); e=t.index('\n}\n',i); fn=t[s:e]
for spec in sys.argv[3:]:
    n,sz,b=spec.split(':')
    m=re.search(r'^(\s+)%'+re.escape(b)+r' = alloca ',fn,re.M); assert m,b
    fn=fn[:m.start()]+'%s%%%s = alloca [%s x i8], align 1\n'%(m.group(1),n,sz)+fn[m.start():]
    last=list(re.finditer(r'^\s+%[\w.$"]+ = alloca .*$',fn,re.M))[-1]
    fn=fn[:last.end()]+'\n  store volatile i8 0, ptr %%%s, align 1'%n+fn[last.end():]
open(sys.argv[2],'w').write(t[:s]+fn+t[e:])
