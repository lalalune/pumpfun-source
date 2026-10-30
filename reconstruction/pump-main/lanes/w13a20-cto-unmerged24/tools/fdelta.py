#!/usr/bin/env python3
"""fdelta.py <m.o>: align orig vs candidate with frame offsets/regs masked; histogram of (orig_off - cand_off) per 0x400 region and per orig frame offset band."""
import sys,re,subprocess,os,difflib,collections
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w13a20-cto-unmerged24')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
def norm(s):
    s=re.sub(r'\s+<[^>]*>','',s.strip())
    if s.startswith('call'): s='call'
    s=re.sub(r'^lddw (r\d+), .*',r'lddw \1',s)
    s=re.sub(r'^(j\w+ .*?)([+-]0x[0-9a-f]+|[+-]\d+)$',r'\1J',s) if s.startswith('j') else s
    s=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',s); s=re.sub(r'add64 (r\d+), -0x[0-9a-f]+',r'add64 \1, -F',s)
    s=re.sub(r'\br\d\b','r',s)
    return s
def off(s):
    m=re.search(r'r10 - 0x([0-9a-f]+)',s)
    if m: return int(m.group(1),16)
    m=re.match(r'add64 r\d, -0x([0-9a-f]+)',s.strip())
    if m: return int(m.group(1),16)
orig=[]
for l in open(OUT+'/orig.dis'):
    m=re.match(r'^(0x[0-9a-f]+)\s+(.*)$',l)
    if m: orig.append((int(m.group(1),16)-0x22a10,m.group(2)))
p=sys.argv[1]
h=subprocess.run([SDK+'/llvm-objdump','-h',p],capture_output=True,text=True).stdout
sec=re.search(r'(\.text\.\S*admin_cto7execute\S*)',h).group(1)
raw=subprocess.run([SDK+'/llvm-objdump','-d','--no-show-raw-insn',p,'--section='+sec],capture_output=True,text=True).stdout
cand=[(int(m.group(1))*8,m.group(2)) for m in (re.match(r'^\s*(\d+):\s+(.*)$',l) for l in raw.splitlines()) if m]
a=[norm(s) for _,s in orig]; b=[norm(s) for _,s in cand]
sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
pairs=collections.Counter(); byreg=collections.defaultdict(collections.Counter)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag!='equal': continue
    for k in range(i2-i1):
        oo=off(orig[i1+k][1]); co=off(cand[j1+k][1])
        if oo is None or co is None: continue
        pairs[(oo,co)]+=1; byreg[orig[i1+k][0]//0x800][oo-co]+=1
print('skeleton ratio',round(sm.ratio(),4))
for r in sorted(byreg): print(hex(r*0x800), byreg[r].most_common(4))
if '--pairs' in sys.argv:
    m=collections.defaultdict(collections.Counter)
    for (oo,co),n in pairs.items(): m[oo][co]+=n
    for oo in sorted(m): print(hex(oo),' '.join('%s:%d'%(hex(c),n) for c,n in m[oo].most_common(3)), ' d=%d'%(oo-m[oo].most_common(1)[0][0]))
