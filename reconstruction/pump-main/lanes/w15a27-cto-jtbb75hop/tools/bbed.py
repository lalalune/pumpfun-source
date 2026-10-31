#!/usr/bin/env python3
"""bbed.py <in.ll> <out.ll> <fn-substr> <block> <newbody-file>: replace a block's non-phi, non-terminator body in fn."""
import sys,re
i,o,fn,blk,nb=sys.argv[1:6]; t=open(i).read()
s=t.find('define'); 
m=re.search(r'^define[^\n]*'+re.escape(fn)+r'[^\n]*$',t,re.M); a=m.start(); b=t.find('\n}\n',a)
F=t[a:b]; p=F.find('\n'+blk+':'); q=F.find('\n\n',p)
B=F[p:q].split('\n'); hdr=[l for l in B if l.startswith(blk+':') or ' = phi ' in l or l==''] ; term=B[-1]
new='\n'.join(hdr)+'\n'+open(nb).read().rstrip('\n')+'\n'+term
F=F[:p]+new+F[q:]; open(o,'w').write(t[:a]+F+t[b:])
