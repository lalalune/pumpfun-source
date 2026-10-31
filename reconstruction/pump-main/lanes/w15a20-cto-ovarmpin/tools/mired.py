#!/usr/bin/env python3
# mired.py <in.mir> <out.mir> <blk,blk,...> <old> <new> : replace a line (exact, stripped) in given blocks
import sys,re
src,dst,bl,old,new=sys.argv[1:6]; bl=set(int(x) for x in bl.split(','))
out=[];cur=None;n=0
for l in open(src):
    m=re.match(r'^  bb\.(\d+)',l)
    if m: cur=int(m.group(1))
    if cur in bl and l.strip()==old:
        l=l.replace(old,new); n+=1
    out.append(l)
open(dst,'w').writelines(out); print('replaced',n,file=sys.stderr)
