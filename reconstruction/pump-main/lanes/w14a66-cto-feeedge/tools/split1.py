#!/usr/bin/env python3
"""split1.py in.ll out.ll PRED 'body;body' : split the PRED -> '+J+' edge with one block holding the given IR lines."""
import sys,re
import os; J=os.environ.get('J','bb74'); src,dst,p=sys.argv[1:4]; body=[x for x in sys.argv[4].split(';') if x.strip()] if len(sys.argv)>4 else []
t=open(src).read()
k=t.index('\n'+p+':'); e=t.index('\n\n',k+1); b=t[k:e]; term=b.rstrip().split('\n')[-1]
nb=J+'.s'+p.replace('.','_'); t=t[:k]+b[:b.rindex(term)]+term.replace('label %'+J+'','label %'+nb)+t[e:]
i=t.index('\n'+J+':'); j=t.index('\n\n',i+1); hb=t[i:j]
hb=re.sub(r', %'+re.escape(p)+r' \]',', %'+nb+' ]',hb); hb=re.sub(r'(; preds = .*)%'+re.escape(p)+r'\b',r'\1%'+nb,hb,count=1)
t=t[:i]+'\n'+nb+':\n'+''.join('  '+x.strip()+'\n' for x in body)+'  br label %'+J+'\n'+hb+t[j:]
open(dst,'w').write(t)
