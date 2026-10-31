#!/usr/bin/env python3
"""gatew.py <src rx> <out> <a> <b> [moves]: put !prof branch_weights a:b on the sweep gate br (bb34) of a post-opt IR (instnamed), optional block moves, llc, score."""
import sys,os,re,subprocess,json
sys.path.insert(0,os.path.dirname(__file__)); import oracle
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w15a13-cto-jointraceback')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
src,name,a,b,*moves=sys.argv[1:]
t=open(f'{OUT}/rx/{src}/m.named.ll').read()
m=re.search(r'^define[^\n]*admin_cto7execute[^\n]*\{\n',t,re.M); s=m.end(); e=t.index('\n}\n',s)
body=t[s:e]
i=body.index('\nbb34:'); j=body.index('\n\n',i); blk=body[i:j]
blk2=re.sub(r'(br i1 %[\w.]+, label %\w+, label %\w+)',r'\1, !prof !99991',blk,count=1); assert blk2!=blk
body=body[:i]+blk2+body[j:]
lines=body.split('\n'); blocks=[['__e',[]]]
for l in lines:
    mm=re.match(r'^([A-Za-z0-9_.$"-]+):',l)
    if mm: blocks.append([mm[1],[]])
    blocks[-1][1].append(l)
for mv in moves:
    x,y=mv.split(':'); n=[q[0] for q in blocks]; bl=blocks.pop(n.index(x)); n=[q[0] for q in blocks]; blocks.insert(n.index(y)+1,bl)
body='\n'.join(l for q in blocks for l in q[1])
t=t[:s]+body+t[e:]+f'\n!99991 = !{{!"branch_weights", i32 {a}, i32 {b}}}\n'
d=f'{OUT}/rx/{name}'; os.makedirs(d,exist_ok=True); open(d+'/m.ll','w').write(t)
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
cand=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(cand)
rr,sd=oracle.metric(cand,oracle.orig_window()); os.remove(d+'/m.ll')
print(json.dumps({'name':name,'ratio':round(rr,5),'bytes':len(cand),'slots_diff':sd}))
