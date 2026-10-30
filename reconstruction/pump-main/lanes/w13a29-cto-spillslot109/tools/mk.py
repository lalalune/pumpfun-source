#!/usr/bin/env python3
"""mk.py <name> <base_var_dir> gene1,gene2,...  [extra_edits.py]: copy base crate, apply genes (genes13 lib) + extra EDITS."""
import sys,os,runpy,subprocess
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w13a29-cto-spillslot109')
name,base,genes=sys.argv[1],sys.argv[2],[g for g in sys.argv[3].split(',') if g and g!='-']
G=runpy.run_path(O+'/x/genes13.py')['GENES']
d=O+'/var/'+name
subprocess.run(['rm','-rf',d]); subprocess.run(['rsync','-a','--exclude','target',base.rstrip('/')+'/',d+'/'],check=True)
f=d+'/src/creator/admin_cto.rs'; s=open(f).read(); n0=s.count('\n')
subs=[x for g in genes for x in G[g]]
X=runpy.run_path(sys.argv[4]) if len(sys.argv)>4 else {}
if X: subs+=X['EDITS']
if X.get('CALL'): s=X['CALL'](s)
for a,b in subs:
    c=s.count(a); assert c==1,(c,a[:100]); s=s.replace(a,b)
assert s.count('\n')==n0
open(f,'w').write(s); print(d)
