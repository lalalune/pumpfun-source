#!/usr/bin/env python3
"""mkslim3.py <noopt.ll> <ex.ll> <out.ll>: keep closure functions (from llvm-extract --recursive output)
and every function that references one; turn all other definitions into declarations."""
import re,sys
full=open(sys.argv[1]).read(); ex=open(sys.argv[2]).read()
defre=re.compile(r'^define (.*?)@("(?:[^"\\]|\\.)+"|[\w.$]+)\((.*)$',re.M)
closure=set(m.group(2) for m in defre.finditer(ex))
linkage={m.group(2):m.group(1) for m in defre.finditer(full)}
internal=set(x for x in closure if re.match(r'(internal|private)\b',linkage.get(x,'')))
refs=re.compile(r'@("(?:[^"\\]|\\.)+"|[\w.$]+)')
lines=full.split('\n'); out=[]; i=0; n=len(lines); kept=0; dropped=0
while i<n:
    l=lines[i]
    if l.startswith('define '):
        m=re.match(r'define (.*?)@("(?:[^"\\]|\\.)+"|[\w.$]+)\(',l)
        nm=m.group(2)
        j=i
        while lines[j]!='}': j+=1
        body='\n'.join(lines[i+1:j])
        if nm in closure or any(r in internal for r in refs.findall(body)):
            out.extend(lines[i:j+1]); kept+=1
        else:
            d=l[len('define '):].rstrip()
            d=d[:-1].rstrip()
            d=re.sub(r'^(internal|private|linkonce_odr|weak_odr|dso_local|hidden)\s+','',d)
            d=re.sub(r'^(internal|private|linkonce_odr|weak_odr|dso_local|hidden)\s+','',d)
            d=re.sub(r'\s+comdat(\([^)]*\))?','',d)
            d=re.sub(r'\s+personality\s+ptr\s+@\S+','',d)
            d=re.sub(r' (%[\w.$"]+)(?=[,)])','',d)
            out.append('declare '+d); dropped+=1
        i=j+1; continue
    out.append(l); i+=1
open(sys.argv[3],'w').write('\n'.join(out))
print('kept',kept,'dropped',dropped)
