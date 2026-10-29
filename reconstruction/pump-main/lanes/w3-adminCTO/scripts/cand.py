#!/usr/bin/env python3
"""cand.py unstripped.so -> listing of admin_cto::execute like win.py orig (addr  insn)"""
import sys,subprocess,re,os
SDK=os.path.expanduser('~/.cache/solana/v1.52/platform-tools/llvm/bin/')
so=sys.argv[1]; pat=sys.argv[2] if len(sys.argv)>2 else r'admin_cto7execute'
s=subprocess.check_output([SDK+'llvm-readelf','-sW',so],text=True)
for l in s.splitlines():
    f=l.split()
    if len(f)>=8 and re.search(pat,f[7]) and f[3]=='FUNC':
        a=int(f[1],16);n=int(f[2]);break
t=subprocess.check_output([SDK+'llvm-objdump','-d','--no-show-raw-insn',f'--start-address={a:#x}',f'--stop-address={a+n:#x}',so],text=True)
for line in t.splitlines():
    m=re.match(r'^\s*([0-9a-f]+):\s+(.*)$',line)
    if m: print(f'0x{int(m.group(1),16):x}  '+re.sub(r'\s+<[^>]*>','',m.group(2).strip()))
