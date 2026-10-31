#!/usr/bin/env python3
"""split1.py in.ll out.ll PRED 'body;body' : split the PRED -> bb76 edge with one block holding the given IR lines."""
import sys,re
src,dst,p=sys.argv[1:4]; body=[x for x in sys.argv[4].split(';') if x.strip()] if len(sys.argv)>4 else []
t=open(src).read()
k=t.index('\n'+p+':'); e=t.index('\n\n',k+1); b=t[k:e]; term=b.rstrip().split('\n')[-1]
nb='bb76.s'+p.replace('.','_'); t=t[:k]+b[:b.rindex(term)]+term.replace('label %bb76','label %'+nb)+t[e:]
i=t.index('\nbb76:'); j=t.index('\n\n',i+1); hb=t[i:j]
hb=re.sub(r', %'+re.escape(p)+r' \]',', %'+nb+' ]',hb); hb=re.sub(r'(; preds = .*)%'+re.escape(p)+r'\b',r'\1%'+nb,hb,count=1)
t=t[:i]+'\n'+nb+':\n'+''.join('  '+x.strip()+'\n' for x in body)+'  br label %bb76\n'+hb+t[j:]
open(dst,'w').write(t)
