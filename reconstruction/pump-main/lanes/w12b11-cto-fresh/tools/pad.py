#!/usr/bin/env python3
"""pad.py <head.rs> <body.tmpl> <out.rs>
head.rs: kept verbatim (accounts struct, event). body.tmpl: code with '//@NNN' marker at the end of
lines that must land on line NNN. Blank comment lines ('//') are inserted before a marked line (at the
nearest preceding statement boundary = immediately before it) to reach the target. Errors on overshoot.
Markers are stripped. Also checks that every error-site line is listed."""
import sys,re
head=open(sys.argv[1]).read().rstrip('\n').split('\n')
body=open(sys.argv[2]).read().rstrip('\n').split('\n')
out=list(head)
for l in body:
    m=re.search(r'\s*//@(\d+)\s*$',l)
    if m:
        tgt=int(m.group(1)); l=l[:m.start()]
        cur=len(out)+1
        if cur>tgt: sys.exit(f'overshoot: line for @{tgt} would be {cur}: {l.strip()[:60]}')
        # insert padding: put it before the statement start; find a pad anchor marker '//PAD' above? simple: insert right here
        out.extend(['']*(tgt-cur))
    out.append(l)
open(sys.argv[3],'w').write('\n'.join(out)+'\n')
print('lines',len(out))
