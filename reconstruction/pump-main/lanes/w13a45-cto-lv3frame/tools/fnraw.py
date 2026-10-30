#!/usr/bin/env python3
"""fnraw.py <raw.ll> <regex-on-lines> [fnpat]: print matching lines of a function body in a raw IR module."""
import sys,re
t=open(sys.argv[1]).read(); pat=sys.argv[3] if len(sys.argv)>3 else r'admin_cto7execute17h'
m=re.search(r'^define [^\n]*@[^\n]*'+pat+r'[^\n]*\{$',t,re.M); i=m.start(); j=t.index('\n}\n',i)
for l in t[i:j].split('\n'):
    if re.search(sys.argv[2],l): print(l.strip()[:230])
