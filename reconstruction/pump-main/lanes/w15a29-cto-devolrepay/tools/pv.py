#!/usr/bin/env python3
"""pv.py <m.ll> <name> <old> <new> [<old> <new>...]: post-opt IR text edit + stock llc + M (experiment only)."""
import sys,os,subprocess,difflib,json
T='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a29-cto-devolrepay'
exec(open(T+'/tools/rx.py').read().split('OUT=os.environ')[0])
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
a=sys.argv[1:]; t=open(a[0]).read(); name=a[1]; ed=a[2:]
for i in range(0,len(ed),2):
    c=t.count(ed[i]); assert c==1,(c,ed[i]); t=t.replace(ed[i],ed[i+1])
d=T+'/pv/'+name; os.makedirs(d,exist_ok=True); open(d+'/m.ll','w').write(t)
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(name,'ERR',r.stderr[-300:]); sys.exit(1)
c=elf_fn(d+'/m.o',KEEP); open(d+'/fn.bin','wb').write(c); os.remove(d+'/m.o')
O=mask(open(T+'/orig.bin','rb').read()); M=sum(b.size for b in difflib.SequenceMatcher(None,O,mask(c),autojunk=False).get_matching_blocks())
rr,sd=metric(c,open(T+'/orig.bin','rb').read())
print(json.dumps({'name':name,'bytes':len(c),'M':M,'ratio':round(rr,5),'slots':sd}))
