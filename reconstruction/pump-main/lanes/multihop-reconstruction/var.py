# var.py name  < python-edit-script (operates on variable s = file text, L = lines)
import sys,os,shutil,subprocess
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/multihop-reconstruction')
WT='./worktrees/multihop-reconstruction/programs/pump'
name=sys.argv[1]; base=sys.argv[2] if len(sys.argv)>2 else WT
d=f'{O}/src/{name}'
shutil.rmtree(d,ignore_errors=True); shutil.copytree(base,d)
p=f'{d}/src/multi_hop_curve_swap.rs'; s=open(p).read(); n0=s.count('\n')
code=sys.stdin.read()
g={'s':s}; exec(code,g); s=g['s']
assert s.count('\n')==n0, ('line count changed', s.count('\n'), n0)
assert s!=open(p).read(), 'no change'
open(p,'w').write(s)
print(d)
