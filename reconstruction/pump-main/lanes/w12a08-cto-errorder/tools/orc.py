#!/usr/bin/env python3
"""orc.py <in.ll> <outprefix> [llc args...]: llc -> obj -> execute disassembly; prints size, ratio vs orig, errseq.
Ratio approximates target_metric: tokens = instruction text with call imm and lddw imm masked, jump offsets kept relative."""
import sys,subprocess,re,os,difflib
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
OUT=os.environ.get('OUT',os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w12a08-cto-errorder'))
inp,pre=sys.argv[1],sys.argv[2]; extra=sys.argv[3:]
r=subprocess.run([SDK+'/llc','-O3','-filetype=obj','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections']+extra+[inp,'-o',pre+'.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
h=subprocess.run([SDK+'/llvm-objdump','-h',pre+'.o'],capture_output=True,text=True).stdout
sec=re.search(r'(\.text\.\S*admin_cto7execute\S*)',h).group(1)
raw=subprocess.run([SDK+'/llvm-objdump','-d','--no-show-raw-insn',pre+'.o','--section='+sec],capture_output=True,text=True).stdout
rows=[]
for l in raw.splitlines():
    m=re.match(r'^\s*(\d+):\s+(.*)$',l)
    if not m: continue
    o=int(m.group(1))*8; s=re.sub(r'\s+<[^>]*>','',m.group(2).strip())
    m2=re.search(r'([+-]0x[0-9a-f]+|[+-]\d+)$',s)
    if s.startswith('j') and m2: s=s[:m2.start()]+f'@{o+8+int(m2.group(1),0)*8:#x}'
    rows.append((o,s))
with open(pre+'.dis','w') as f:
    for o,s in rows: f.write(f'{o:#06x}  {s}\n')
def toks(rows):
    out=[]
    for o,s in rows:
        s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw \1',s)
        m=re.search(r'@(0x[0-9a-f]+)$',s)
        if m: s=s[:m.start()]+'%+d'%((int(m.group(1),16)-o-8)//8)
        out.append(s)
    return out
def load(f): return [(int(l.split()[0],16),l.split(None,1)[1].strip()) for l in open(f)]
orig=load(OUT+'/an/orig.dis')
a=toks(orig); b=toks(rows)
sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
size=(rows[-1][0]+(16 if rows[-1][1].startswith('lddw') else 8)) if rows else 0
lines=[int(m.group(1),16) for o,s in rows for m in [re.match(r'stw \[r10 - 0x2b8\], (0x[0-9a-f]+)',s)] if m]
print(f'{os.path.basename(pre)}: bytes {size} ratio {sm.ratio():.5f} errseq {" ".join(map(str,lines))}')
