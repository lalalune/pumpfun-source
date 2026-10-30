#!/usr/bin/env python3
"""sodis.py <unstripped.so|orig>: admin_cto::execute disassembly with function-relative byte offsets."""
import sys,subprocess,re,os
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llvm-objdump')
p=sys.argv[1]
if p=='orig':
    for l in open(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a06-cto-sweptcoal/o.dis')):
        a,rest=l.split(None,1); print('%04x %s'%(int(a,16)-0x22a10,rest.rstrip()))
    sys.exit()
t=subprocess.run([SDK,'-t',p],capture_output=True,text=True).stdout
m=[l for l in t.split('\n') if 'admin_cto7execute' in l][0].split()
st=int(m[0],16); sz=int([x for x in m if re.fullmatch('[0-9a-f]{16}',x)][1],16)
d=subprocess.run([SDK,'-d','--no-show-raw-insn','--start-address=%d'%st,'--stop-address=%d'%(st+sz),p],capture_output=True,text=True).stdout
for l in d.split('\n'):
    mm=re.match(r'\s*(\d+):\s+(.*)',l)
    if mm: print('%04x %s'%(int(mm.group(1))*8-st,mm.group(2).strip()))
