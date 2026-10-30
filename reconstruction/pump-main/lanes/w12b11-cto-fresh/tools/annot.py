#!/usr/bin/env python3
"""annot.py <listing.txt> <unstripped.so> : annotate 'call imm' with candidate symbol names (pc-relative)."""
import sys,subprocess,re,os
SDK=os.path.expanduser('~/.cache/solana/v1.52/platform-tools/llvm/bin/')
lst,so=sys.argv[1],sys.argv[2]
s=subprocess.check_output([SDK+'llvm-readelf','-sW','--demangle',so],text=True)
syms={}
for l in s.splitlines():
    f=l.split(None,7)
    if len(f)>=8 and f[3]=='FUNC':
        syms[int(f[1],16)]=f[7]
for line in open(lst):
    line=line.rstrip('\n')
    m=re.match(r'^(0x[0-9a-f]+)\s+call (-?0x[0-9a-f]+)$',line.strip())
    if m:
        pc=int(m.group(1),16); imm=int(m.group(2),16)
        if imm==-1: print(line+'   ; syscall/abort'); continue
        t=pc+8+imm*8
        n=syms.get(t,'?%x'%t)
        n=re.sub(r'::h[0-9a-f]{16}$','',n)
        print(line+'   ; '+n[:110])
    else: print(line)
