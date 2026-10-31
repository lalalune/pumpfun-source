#!/usr/bin/env python3
"""esplit.py in.ll out.ll PRED SUCC [body] : split the PRED->SUCC edge with a new block holding body (default empty asm)."""
import sys,re,hashlib
src,dst,p,s=sys.argv[1:5]; body=sys.argv[5] if len(sys.argv)>5 else 'call void asm sideeffect "", ""()'
t=open(src).read()
nb='es.'+hashlib.md5((p+s).encode()).hexdigest()[:8]
k=t.index('\n'+p+':'); e=t.index('\n\n',k+1); b=t[k:e]; L=b.split('\n'); term=L[-1]
assert term.strip().startswith('br i1'),term
term2=term.replace('label %'+s+',','label %'+nb+',',1) if ('label %'+s+',') in term else term.replace('label %'+s,'label %'+nb,1)
assert term2!=term
L[-1]=term2; t=t[:k]+'\n'.join(L)+t[e:]
i=t.index('\n'+s+':'); j=t.index('\n\n',i+1); hb=t[i:j]
hb=re.sub(r'(\[ [^\]]*?, )%'+re.escape(p)+r'( \])',lambda m:m.group(1)+'%'+nb+m.group(2),hb)
t=t[:i]+'\n'+nb+':\n  '+body+'\n  br label %'+s+'\n'+hb+t[j:]
open(dst,'w').write(t)
