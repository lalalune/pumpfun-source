#!/usr/bin/env python3
# ann.py <so> <syms> <start> <size> : disassembly with call targets annotated (offsets relative to start)
import re,sys,subprocess
import os; B=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
so,symf,start,size=sys.argv[1],sys.argv[2],int(sys.argv[3],16),int(sys.argv[4])
syms={}
for l in open(symf):
    p=l.split(' ',2)
    if len(p)>=3: syms[int(p[0],16)]=re.sub(r'::h[0-9a-f]{16}$','',p[2].strip())
out=subprocess.check_output([B+'/llvm-objdump','-d','--no-show-raw-insn',f'--start-address={start}',f'--stop-address={start+size}',so],text=True)
for l in out.splitlines():
    m=re.match(r'\s*(\d+):\s+(.*)',l)
    if not m: continue
    a=int(m.group(1))*8; ins=re.sub(r'\s*<.*>$','',m.group(2))
    cm=re.match(r'call (-?0x[0-9a-f]+)$',ins)
    if cm:
        v=cm.group(1); imm=int(v,16) if not v.startswith('-') else -int(v[1:],16)
        t=a+8+imm*8; ins+='   ; '+syms.get(t,'?%x'%t)
    print('%#06x  %s'%(a-start,ins))
