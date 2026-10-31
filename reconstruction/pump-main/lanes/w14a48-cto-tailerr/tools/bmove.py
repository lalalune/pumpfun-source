#!/usr/bin/env python3
"""bmove.py <m.ll> <tag> <spec...>: post-opt llc-only oracle. spec = 'BLOCK@BEFORE' moves BLOCK (label) right before
label BEFORE inside execute. Prints json {tag,ratio,bytes,slots_diff}. Experiment only."""
import sys,os,re,subprocess,json,runpy
sys.argv_saved=sys.argv
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a48-cto-tailerr')
rx=runpy.run_path(OUT+'/tools/rx_lib.py')
src,tag,specs=sys.argv[1],sys.argv[2],sys.argv[3:]
t=open(src).read().split('\n')
s=next(i for i,l in enumerate(t) if l.startswith('define') and 'admin_cto7execute' in l)
e=next(i for i in range(s,len(t)) if t[i]=='}')
body=t[s+1:e]
# split into blocks
blocks=[];cur=None;head=[]
for l in body:
    m=re.match(r'^("?[^\s:"]+"?|"[^"]+"):',l)
    if m and not l.startswith(' '):
        cur=[m.group(1).strip('"'),[l]]; blocks.append(cur)
    elif cur is None: head.append(l)
    else: cur[1].append(l)
names=[b[0] for b in blocks]
for sp in specs:
    a,b=sp.split('@')
    ia=names.index(a); blk=blocks.pop(ia); names.pop(ia)
    ib=names.index(b) if b!='END' else len(names)
    blocks.insert(ib,blk); names.insert(ib,a)
nb=head+[x for b in blocks for x in b[1]]
t=t[:s+1]+nb+t[e:]
d=OUT+'/bm/'+tag; os.makedirs(d,exist_ok=True)
open(d+'/m.ll','w').write('\n'.join(t))
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(json.dumps({'tag':tag,'error':r.stderr[-300:]})); sys.exit(0)
cand=rx['elf_fn'](d+'/m.o',rx['KEEP']); open(d+'/fn.bin','wb').write(cand)
rr,sd=rx['metric'](cand,rx['orig_window']())
print(json.dumps({'tag':tag,'ratio':round(rr,5),'bytes':len(cand),'slots_diff':sd}))
os.remove(d+'/m.ll'); os.remove(d+'/m.o')
