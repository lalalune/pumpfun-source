#!/usr/bin/env python3
# objfn.py <obj or so> <symbol substring> [start size]: dump function as 'off  insn' lines (calls/lddw imm kept textual)
import sys,subprocess,re
import os; B=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
p=sys.argv[1]; pat=sys.argv[2]
if len(sys.argv)>3: a=int(sys.argv[3],16); n=int(sys.argv[4]); sec=None
else:
    sy=subprocess.check_output([B+'/llvm-readelf','-sW',p],text=True)
    a=n=None
    for l in sy.splitlines():
        f=l.split()
        if len(f)>=8 and pat in f[7] and f[3]=='FUNC': a=int(f[1],16); n=int(f[2]); name=f[7]; break
args=[B+'/llvm-objdump','-d','--no-show-raw-insn']
if p.endswith('.o'):
    # function sections: find section containing the symbol
    args+=['--section=.text.'+name]
    txt=subprocess.check_output(args+[p],text=True); base=0
else:
    txt=subprocess.check_output(args+['--start-address=%#x'%a,'--stop-address=%#x'%(a+n),p],text=True); base=a
for l in txt.splitlines():
    m=re.match(r'^\s*(\d+):\s+(.*)$',l)
    if m: print('%#06x  %s'%(int(m.group(1))*8-base, re.sub(r'\s*<[^>]*>$','',m.group(2).strip())))
