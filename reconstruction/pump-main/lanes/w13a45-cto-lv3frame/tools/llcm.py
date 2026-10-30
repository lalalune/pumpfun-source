#!/usr/bin/env python3
# llcm.py <m.ll> <name> [llcargs..]: llc a post-opt module and score it (experiment only)
import sys,os,subprocess,json
src=open(os.path.dirname(__file__)+'/rx.py').read().split("a=sys.argv[1:]")[0]
g={'__name__':'rxlib','__file__':__file__}; exec(src,g)
ml,name=sys.argv[1],sys.argv[2]; d=g['OUT']+'/rx/'+name; os.makedirs(d,exist_ok=True)
if os.path.abspath(ml)!=os.path.abspath(d+'/m.ll'): subprocess.run(['cp',ml,d+'/m.ll'])
r=subprocess.run([g['SDK']+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o',*sys.argv[3:]],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
c=g['elf_fn'](d+'/m.o',g['KEEP']); open(d+'/fn.bin','wb').write(c)
rr,sd=g['metric'](c,g['orig_window']()); print(json.dumps({'name':name,'ratio':round(rr,5),'bytes':len(c),'slots_diff':sd}))
