#!/usr/bin/env python3
# tsites.py <xdir>... : which error lines have an outlined ToString call (from ex.o relocations)
import sys,re,subprocess,os
B=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
for d in sys.argv[1:]:
    ll=open(d+'/ex.ll').read(); S=re.search(r'^define[^@]*@(_ZN14pump_recovered9admin_cto7execute\w*)',ll,re.M).group(1)
    t=subprocess.check_output([B+'/llvm-objdump','-dr','--no-show-raw-insn','--section=.text.'+S,d+'/ex.o'],text=True).split('\n')
    out=[]
    for i,l in enumerate(t):
        if 'R_SBF_64_32' in l and 'ToString' in l:
            ln=None
            for j in range(i,min(len(t),i+150)):
                m=re.search(r'\*\(u32 \*\)\(r10 - 0x[0-9a-f]+\) = (0x1[0-9a-f]{2}|0x2[0-9a-f]{2})\b',t[j]) or re.search(r'stw \[r10 - 0x[0-9a-f]+\], (0x1[0-9a-f]{2}|0x2[0-9a-f]{2})\b',t[j])
                if m: ln=int(m.group(1),16); break
            out.append(ln)
    print(os.path.basename(d.rstrip('/')),'outlined to_string lines:',sorted(x for x in out if x) , 'n',len(out))
