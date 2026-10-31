#!/usr/bin/env python3
"""irmv.py <m.ll> <name> X>Y ... : move IR block X (with its whole body) to right after block Y in execute; llc; score."""
import sys,re,os,subprocess,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import sc
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
src,name=sys.argv[1],sys.argv[2]; L=open(src).read().split('\n')
fs=[i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto7execute' in l][0]
fe=[i for i in range(fs,len(L)) if L[i]=='}'][0]
def short(l):
    m=re.match(r'^("?[^":]+"?):',l)
    if not m: return None
    s=m.group(1).strip('"')
    if 'to_string' in s: s=s.split('E.')[-1]
    return s
starts=[i for i in range(fs+1,fe) if short(L[i])]
blocks=[]; head=L[fs:starts[0]]
for a,b in zip(starts,starts[1:]+[fe]): blocks.append((short(L[a]),L[a:b]))
for mv in sys.argv[3:]:
    x,y=mv.split('>'); bx=[b for b in blocks if b[0]==x][0]; blocks.remove(bx)
    k=[i for i,b in enumerate(blocks) if b[0]==y][0]; blocks.insert(k+1,bx)
out=L[:fs]+head+sum([b[1] for b in blocks],[])+L[fe:]
d=T+'/../tmp/p'; os.makedirs(d,exist_ok=True); open(f'{d}/{name}.ll','w').write('\n'.join(out))
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',f'{d}/{name}.ll','-filetype=asm','-o',f'{d}/{name}.s'],capture_output=True,text=True)
if r.returncode: sys.exit(r.stderr[-2000:])
s=sc.score(f'{d}/{name}.s'); s.pop('ch'); print(name,json.dumps(s))
q=subprocess.run(['python3',T+'/seq.py',f'{d}/{name}.s','bb6.i','24'],capture_output=True,text=True).stdout
print('   ',' '.join(l.split()[0] for l in q.split('\n') if l.strip()))
