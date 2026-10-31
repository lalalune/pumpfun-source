#!/usr/bin/env python3
"""ocalls.py <rx dir> [lo hi]: execute calls in m.o with window offsets and short names"""
import sys,subprocess,re,os
OBJ=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llvm-objdump')
d=sys.argv[1]; lo=int(sys.argv[2],16) if len(sys.argv)>2 else 0; hi=int(sys.argv[3],16) if len(sys.argv)>3 else 1<<30
t=subprocess.run([OBJ,'-dr','--no-show-raw-insn','-C',d+'/m.o'],capture_output=True,text=True).stdout.split('\n')
on=False
for l in t:
    if re.match(r'^[0-9a-f]+ <pump_recovered::admin_cto::execute::',l): on=True; continue
    if on and re.match(r'^[0-9a-f]+ <(?!LBB)',l): break
    if not on: continue
    m=re.match(r'\s+([0-9a-f]+):\s+R_SBF_\S+\s+(.*)',l)
    if m:
        o=int(m.group(1),16)
        if lo<=o<hi:
            nm=re.sub(r'::h[0-9a-f]{16}$','',m.group(2)); print('%04x %s'%(o,'::'.join(nm.split('::')[-3:])[:80]))
