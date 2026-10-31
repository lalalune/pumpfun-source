#!/usr/bin/env python3
# mired2.py <in.mir> <out.mir> <del-blocks> <del-regex> <ins-block> <ins-line>: delete matching lines in blocks, insert a line at top of a block body
import sys,re
src,dst,bl,rx,ib,il=sys.argv[1:7]; bl=set(int(x) for x in bl.split(',')); ib=int(ib)
out=[];cur=None;nd=0;pend=False
for l in open(src):
    m=re.match(r'^  bb\.(\d+)',l)
    if m: cur=int(m.group(1)); pend=(cur==ib)
    if cur in bl and re.fullmatch(rx,l.strip()): nd+=1; continue
    if pend and l.strip()=='' :
        out.append(l); out.append('    '+il+'\n'); pend=False; continue
    out.append(l)
open(dst,'w').writelines(out); print('deleted',nd,file=sys.stderr)
