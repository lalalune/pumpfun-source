#!/usr/bin/env python3
"""reduce.py in.ll out.ll : keep only create_token_account_v2 body; other defines -> declares."""
import sys,re
t=open(sys.argv[1]).read()
out=[];i=0
lines=t.split('\n')
n=len(lines);k=0
while k<n:
    l=lines[k]
    if l.startswith('define '):
        if 'create_token_account_v217h' in l:
            while True:
                out.append(lines[k])
                if lines[k]=='}': break
                k+=1
        else:
            h=l[len('define '):]
            h=h.rsplit('{',1)[0]
            h=re.sub(r'\b(internal|private|dso_local|linkonce_odr|weak_odr|hidden|unnamed_addr|local_unnamed_addr)\b','',h)
            h=re.sub(r'\s+personality\s+ptr\s+@\S+','',h)
            h=re.sub(r'\s+section\s+"[^"]*"','',h)
            h=re.sub(r'\s+comdat(\([^)]*\))?','',h)
            h=re.sub(r'\s+!dbg\s+!\d+','',h)
            out.append('declare '+h.strip())
            while lines[k]!='}': k+=1
    elif ' alias ' in l and l.startswith('@'):
        pass
    else:
        out.append(l)
    k+=1
open(sys.argv[2],'w').write('\n'.join(out))
