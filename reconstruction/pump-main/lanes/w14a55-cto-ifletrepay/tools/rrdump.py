# rrdump.py <mn.ll> <name> X:off[,X:off]  -> rx/<name>/fn.bin and m.ll (re-read variant)
import sys,os,subprocess
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/reread.py').read().split('singles=[]')[0]
mll,name,spec=sys.argv[1:4]
sys.argv=['x',mll,'/dev/null']; g={'__file__':T+'/reread.py'}; exec(src,g)
job=[(s.split(':')[0],int(s.split(':')[1])) for s in spec.split(',')]
d=os.path.dirname(T)+'/rx/'+name; os.makedirs(d,exist_ok=True); open(d+'/m.ll','w').write(g['build'](job))
subprocess.run([g['SDK']+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],check=True)
open(d+'/fn.bin','wb').write(g['g']['elf_fn'](d+'/m.o',g['g']['KEEP'])); print(d)
