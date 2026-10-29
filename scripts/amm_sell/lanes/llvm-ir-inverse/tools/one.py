import sys, json; sys.path.insert(0,'tools'); import irfn, irscore
# usage: one.py FN.ll OUTTAG "move NAME after NAME2" ...
f=irfn.Fn(sys.argv[1])
o=list(f.order0)
for spec in sys.argv[3:]:
    a,b=spec.split('>>')   # move a right after b
    o=[x for x in o if x!=a]; o.insert(o.index(b)+1,a)
txt=irfn.render(f.head,[(n,f.blocks[n]) for n in o])
open(f'runs/{sys.argv[2]}.fn.ll','w').write(txt)
import subprocess, pathlib
wd=pathlib.Path('runs'); ll=wd/f'{sys.argv[2]}.ll'; ll.write_text(pathlib.Path(f.hp).read_text()+txt)
subprocess.run([str(irfn.B/'llvm-as'),str(ll),'-o',str(wd/(sys.argv[2]+'.bc'))],check=True)
subprocess.run(irfn.LLC+[str(wd/(sys.argv[2]+'.bc')),'-o',str(wd/(sys.argv[2]+'.o'))],check=True,capture_output=True)
ll.unlink()
r=irscore.score(wd/(sys.argv[2]+'.o'),True); d=r.pop('diff'); print(json.dumps(r)); print('\n'.join(d))
