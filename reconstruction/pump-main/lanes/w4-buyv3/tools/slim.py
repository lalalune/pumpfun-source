#!/usr/bin/env python3
"""slim.py module.ll SYM_SUBSTR out.ll : keep only the definition containing SYM_SUBSTR, turn other defines into declares."""
import sys,re
src,sym,out=sys.argv[1:4]
L=open(src).read().split('\n'); o=[]; i=0
while i<len(L):
    l=L[i]
    if l.startswith('define '):
        j=i
        while L[j]!='}': j+=1
        if sym in l: o+=L[i:j+1]
        else:
            h=l[len('define '):]
            h=re.sub(r'\s*\{$','',h)
            h=re.sub(r'\s+(personality\s+ptr\s+@\S+|comdat(\(\$[^)]*\))?|section\s+"[^"]*"|align \d+$|prefix\s+\S+)','',h)
            h=re.sub(r' #\d+',' ',h)
            h=re.sub(r'\b(internal|private)\b ','',h)
            o.append('declare '+h)
        i=j+1; continue
    if re.match(r'^@\S+ = .*\balias\b',l): i+=1; continue
    o.append(l); i+=1
open(out,'w').write('\n'.join(o))
