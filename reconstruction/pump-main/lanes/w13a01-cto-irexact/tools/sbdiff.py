#!/usr/bin/env python3
"""sbdiff.py <m.o|unstripped.so> [--frame] [--ctx N] [--from 0xOFF --to 0xOFF]: side-by-side diff of orig admin_cto vs candidate.
--frame masks r10 offsets. Jumps become relative +N. Calls masked to names when available."""
import sys,re,subprocess,os,difflib
OUT=os.environ.get('RX_OUT',os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w13a01-cto-irexact'))
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
a=sys.argv[1:]; path=a.pop(0); frame='--frame' in a; ctx=int(a[a.index('--ctx')+1]) if '--ctx' in a else 0
lo=int(a[a.index('--from')+1],16) if '--from' in a else 0; hi=int(a[a.index('--to')+1],16) if '--to' in a else 1<<30
def norm(o,s):
    s=re.sub(r'\s+<[^>]*>','',s.strip())
    if s.startswith('call') or s.startswith('callx'): s='call'
    s=re.sub(r'^lddw (r\d+), .*',r'lddw \1',s)
    m=re.match(r'^(j\w+ .*?)([+-]0x[0-9a-f]+|[+-]\d+)$',s)
    if s.startswith('j') and m: s=m.group(1)+'%+d'%(int(m.group(2),0))
    if frame: s=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',s)
    return s
orig=[]
for l in open(OUT+'/orig.dis'):
    m=re.match(r'^(0x[0-9a-f]+)\s+(.*)$',l)
    if m: orig.append((int(m.group(1),16)-0x22a10,m.group(2)))
if path.endswith('.o'):
    h=subprocess.run([SDK+'/llvm-objdump','-h',path],capture_output=True,text=True).stdout
    sec=re.search(r'(\.text\.\S*admin_cto7execute\S*)',h).group(1)
    raw=subprocess.run([SDK+'/llvm-objdump','-d','--no-show-raw-insn',path,'--section='+sec],capture_output=True,text=True).stdout
    cand=[]
    for l in raw.splitlines():
        m=re.match(r'^\s*(\d+):\s+(.*)$',l)
        if m: cand.append((int(m.group(1))*8,m.group(2)))
else:
    sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a01-cto-irexact/reconstruction/harness')
    raise SystemExit('so not supported yet')
# objdump of .o with relocations shows jumps as +off in slots; orig.dis shows jump targets? normalize both to relative
def rel(rows):
    out=[]
    for o,s in rows:
        s2=re.sub(r'\s+<[^>]*>','',s.strip())
        m=re.match(r'^(j\w+ .*?)(0x[0-9a-f]+)$',s2)
        if s2.startswith('j') and m and not re.search(r'[+-]\s*0x',s2[-12:]):
            s2=m.group(1)+'%+d'%((int(m.group(2),16)-0x22a10-o-8)//8)
        out.append((o,norm(o,s2)))
    return out
O=rel(orig); Cn=[(o,norm(o,s)) for o,s in cand]
ot=[s for _,s in O]; ct=[s for _,s in Cn]
sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False)
print('ratio',round(sm.ratio(),5),'orig',len(ot),'cand',len(ct))
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal':
        if ctx and i2-i1>2*ctx:
            if O[i1][0]>=lo and O[i1][0]<hi: print('    ... %d equal ...'%(i2-i1))
        continue
    if O[min(i1,len(O)-1)][0]<lo or O[min(i1,len(O)-1)][0]>=hi: continue
    print(f'@@ orig {O[min(i1,len(O)-1)][0]:#06x} cand {Cn[min(j1,len(Cn)-1)][0]:#06x} {tag} {i2-i1}/{j2-j1}')
    for k in range(i1,i2): print(f'-  {O[k][0]:#06x}  {O[k][1]}')
    for k in range(j1,j2): print(f'+  {Cn[k][0]:#06x}  {Cn[k][1]}')
