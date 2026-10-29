import sys,os;sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w4-sellv2-b/scripts')
import irlib,runpy
def edit(t):
    if os.environ.get('MOVES'): t=runpy.run_path('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w4-sellv2-b/edits/moves.py')['edit'](t)
    blk=os.environ.get('PBLK','bb208.i'); perm=[int(x) for x in os.environ['PERM']]
    pre,parts,post=irlib.split(t)
    for i,p in enumerate(parts):
        if irlib.label(p)==blk:
            L=p.split('\n'); idx=[k for k,l in enumerate(L) if ' = phi ' in l]
            ph=[L[k] for k in idx]
            for k,j in zip(idx,perm): L[k]=ph[j]
            parts[i]='\n'.join(L)
    return irlib.join(pre,parts,post)
