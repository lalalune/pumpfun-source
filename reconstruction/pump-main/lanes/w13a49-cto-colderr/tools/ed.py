#!/usr/bin/env python3
"""ed.py <m.ll> <edit.py|-> [spec] [--keep DIR]: apply edit(fn_text) from edit.py to execute's post-opt IR, then bwfm.run spec."""
import sys,os,runpy,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import bwx,bwfm
a=sys.argv[1:]; keep=None
if '--keep' in a: i=a.index('--keep'); keep=a[i+1]; del a[i:i+2]
mod=open(a[0]).read(); e=a[1]; spec=a[2] if len(a)>2 else ''
if e!='-':
    pre,fn,post=bwx.split(mod)
    for ee in e.split(','): fn=runpy.run_path(ee)['edit'](fn)
    mod=pre+fn+post
print(json.dumps(bwfm.run(mod,spec,bwx.orig_toks(),keep)))
