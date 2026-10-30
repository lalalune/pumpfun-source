#!/usr/bin/env python3
"""Diagnostic: build a minimal module containing only v3_buy_costs (callees declared) from a full .ll."""
import re,sys
src,dst=sys.argv[1],sys.argv[2]
t=open(src).read()
m=re.search(r'^define[^\n]*12v3_buy_costs[^\n]*\{\n.*?^\}\n',t,re.M|re.S); f=m.group(0)
f=re.sub(r', !(noalias|alias\.scope|noundef|nonnull|align|dbg) ![0-9]+','',f)
hdr=[l for l in t.split('\n')[:20] if l.startswith(('target datalayout','target triple'))]
names=set(re.findall(r'@("[^"]+"|[\w.$]+)',f)); names.discard(re.search(r'@(\S+?)\(',f).group(1))
decls=[]
for n in sorted(names):
    if n.startswith('llvm.'): 
        mm=re.search(r'^declare[^\n]*@'+re.escape(n)+r'\(.*$',t,re.M); decls.append(mm.group(0)); continue
    mm=re.search(r'^(define|declare)([^\n]*@'+re.escape(n)+r'\([^\n]*?)\s*(\{|$)',t,re.M)
    if mm:
        s=mm.group(2); s=re.sub(r'\b(internal|private|dso_local|unnamed_addr)\b','',s)
        s=re.sub(r'#\d+','',s)
        decls.append('declare'+s); continue
    gm=re.search(r'^@'+re.escape(n)+r' = .*$',t,re.M)
    if gm: decls.append('@'+n+' = external global [0 x i8]'); continue
    raise SystemExit('missing '+n)
attrs=sorted(set(re.findall(r'#(\d+)',f)))
al=[re.search(r'^attributes #'+a+r' = .*$',t,re.M).group(0) for a in attrs]
mds=sorted(set(re.findall(r'!(\d+)',f)),key=int)
ml=[]
for md in mds:
    mm=re.search(r'^!'+md+r' = .*$',t,re.M); ml.append(mm.group(0))
open(dst,'w').write('\n'.join(hdr)+'\n\n'+'\n'.join(decls)+'\n\n'+f+'\n'+'\n'.join(al)+'\n'+'\n'.join(ml)+'\n')
