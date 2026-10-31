#!/usr/bin/env python3
"""mvir.py in.ll out.ll BLK AFTER [SPEC]: move IR block BLK to right after block AFTER in execute (IR order only), then apply bwx SPEC."""
import sys,os
sys.path.insert(0,os.path.dirname(__file__)); import bwx
src,dst,blk,after=sys.argv[1:5]; spec=sys.argv[5] if len(sys.argv)>5 else ''
import re
mod=open(src).read(); pre,fn,post=bwx.split(mod); fn=re.sub(r'%(\d+)\b',r'%v\1',fn); head,bl,tail=bwx.blocks(fn)
for b in blk.split('+'):
    i=[k for k,x in enumerate(bl) if x[0]==b][0]; x=bl.pop(i)
    j=[k for k,y in enumerate(bl) if y[0]==after][0]; bl.insert(j+1,x); after=b
fn='\n'.join([head]+[l for _,x in bl for l in x]+[tail])+'\n'
open(dst,'w').write(bwx.apply(pre+fn+post,spec) if spec else pre+fn+post)
