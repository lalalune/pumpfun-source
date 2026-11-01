#!/usr/bin/env python3
"""Block-order oracle. usage: reorder.py OUTNAME op... ; op = 'X>Y' (move block X right after Y) or 'list'
Writes oracle/OUTNAME.ll, runs llc, compares normalized cashback code with original. Prints difflines."""
import sys,re,subprocess,os
HERE=os.path.dirname(os.path.abspath(__file__)); OR=os.path.join(HERE,'..','oracle')
B='$HOME/Documents/Codex/2026-10-24/amm-sell-swarm/infra/sdk-native/rust/lib/rustlib/aarch64-apple-darwin/bin'
SYM='_ZN18pump_amm_recovered12instructions4swap4sell8cashback17hccb72da5245169afE'
src=os.environ.get('BASE_LL',os.path.join(OR,'base.ll'))
lines=open(src).read().split('\n')
s=next(i for i,l in enumerate(lines) if l.startswith('define') and SYM in l)
e=next(i for i in range(s,len(lines)) if lines[i]=='}')
body=lines[s+1:e]
blocks=[];cur=['entry',[]]
for l in body:
    m=re.match(r'^([0-9]+):',l)
    if m:
        blocks.append(cur); cur=[m.group(1),[l]]
    else: cur[1].append(l)
blocks.append(cur)
name=sys.argv[1]; ops=sys.argv[2:]
if ops==['list']:
    for n,bl in blocks:
        calls=[re.search(r'@"?([^"(]+)',x).group(1)[-40:] for x in bl if ' call ' in x and 'lifetime' not in x]
        term=[x.strip()[:60] for x in bl if x.strip().startswith(('br ','switch','ret','unreachable'))]
        print(n, len(bl), term, calls[:3])
    sys.exit()
for op in ops:
    if op.startswith('split:'):
        # split:P:S:Y[:alloca]  new block on edge P->S placed after Y, with optional lifetime.end of %alloca
        _,P,S,Y,*A=op.split(':'); nb='x'+P
        bp=next(b for b in blocks if b[0]==P)
        bp[1]=[re.sub(r'label %'+S+r'\b','label %'+nb,l) if l.strip().startswith(('br ','switch')) or l.strip().startswith('i64') else l for l in bp[1]]
        bs=next(b for b in blocks if b[0]==S)
        bs[1]=[re.sub(r'%'+P+r' \]','%'+nb+' ]',l) if ' phi ' in l else l for l in bs[1]]
        bs[1][0]=bs[1][0].replace('%'+P,'%'+nb) if 'preds' in bs[1][0] else bs[1][0]
        body=[nb+':']+(['  call void @llvm.lifetime.end.p0(i64 %s, ptr nonnull %%%s)'%(A[1] if len(A)>1 else '8',A[0])] if A and A[0] else [])+['  br label %'+S]
        iy=next(i for i,b in enumerate(blocks) if b[0]==Y); blocks.insert(iy+1,[nb,body]); continue
    x,y=op.split('>')
    bx=next(b for b in blocks if b[0]==x); blocks.remove(bx)
    iy=next(i for i,b in enumerate(blocks) if b[0]==y); blocks.insert(iy+1,bx)
# entry must stay first; blocks need label lines; entry has none
ren=lambda t: re.sub(r'^([0-9]+):', r'v\1:', re.sub(r'%([0-9]+)\b', r'%v\1', t))
out=lines[:s]+[ren(lines[s])]
for n,bl in blocks: out+=[ren(x) for x in bl]
out+=lines[e:]
p=os.path.join(OR,name+'.ll'); open(p,'w').write('\n'.join(out))
o=os.path.join(OR,name+'.o')
r=subprocess.run([B+'/llc','-O3','-mtriple=sbf','-mattr=+store-imm,+jmp-ext','-relocation-model=pic','-function-sections','-data-sections','-filetype=obj',p,'-o',o],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
sp=os.path.join(OR,name+'.s')
subprocess.run(os.path.join(HERE,'fdis.sh')+' '+o+' > '+sp,shell=True)
os.remove(p) if not os.environ.get('KEEP') else None
subprocess.run(['python3',os.path.join(HERE,'norm.py'),os.path.join(OR,'orig.s'),sp]+([os.environ['SHOW']] if os.environ.get('SHOW') else []))
