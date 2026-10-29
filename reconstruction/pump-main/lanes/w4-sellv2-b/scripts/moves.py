# MOVES="after:blk:tgt;before:blk:tgt;end:blk"  ; also QM4=1 applies qm4
import sys,os;sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w4-sellv2-b/scripts')
import irlib,runpy
def edit(t):
    if os.environ.get('QM4')=='1': t=runpy.run_path('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w4-sellv2-b/edits/qm4.py')['edit'](t)
    for m in filter(None,os.environ.get('MOVES','').split(';')):
        k=m.split(':')
        if k[0]=='end':
            pre,parts,post=irlib.split(t); t=irlib.move_after(t,k[1],irlib.label(parts[-1]))
        elif k[0]=='after': t=irlib.move_after(t,k[1],k[2])
        elif k[0]=='before': t=irlib.move_before(t,k[1],k[2])
    return t
