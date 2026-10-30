#!/usr/bin/env python3
# errsites.py <ann.txt> <so> : for each PumpError::name call: variant (from lddw r2 const), to_string mode, line immediate
import re,sys,struct,subprocess
import os; B=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
lines=[l.rstrip('\n') for l in open(sys.argv[1])]
data=open(sys.argv[2],'rb').read()
out=subprocess.check_output([B+'/llvm-readelf','-S',sys.argv[2]],text=True)
S={}
for l in out.splitlines():
    m=re.search(r'\]\s+(\S+)\s+\S+\s+([0-9a-f]{16})\s+([0-9a-f]+)\s+([0-9a-f]+)',l)
    if m: S[m.group(1)]=(int(m.group(2),16),int(m.group(3),16),int(m.group(4),16))
rb,ro,rs=S['.rodata']
def rd32(v): return struct.unpack('<I',data[ro+(v-rb):ro+(v-rb)+4])[0]
res=[]
for i,l in enumerate(lines):
    if 'PumpError::name' in l or 'ErrorCode::name' in l:
        var=None
        for j in range(i-1,max(0,i-6),-1):
            m=re.search(r'lddw r2, (0x[0-9a-f]+)',lines[j])
            if m: var=rd32(int(m.group(1),16)); break
        mode='?'; ln=None
        for j in range(i+1,min(len(lines),i+60)):
            if 'to_string' in lines[j]: mode='OUT'; break
            if 'Display$GT$::fmt' in lines[j]: mode='INL'; break
        # line immediate: look for 'stw [r10 - ...], 0x...' with plausible line after
        for j in range(i+1,min(len(lines),i+90)):
            m=re.search(r'stw \[r\d+ [-+] 0x[0-9a-f]+\], (0x[0-9a-f]+)$',lines[j])
            if m:
                v=int(m.group(1),16)
                if 200<v<800: ln=v; break
        res.append((lines[i].split()[0],var,mode,ln))
for r in res: print(*r)
