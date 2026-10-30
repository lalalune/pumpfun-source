#!/usr/bin/env python3
"""fndiff.py a.o b.o : list functions whose normalized disassembly differs."""
import subprocess,sys,re,os
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools')
def fns(p):
    out=subprocess.run([SDK+'/llvm/bin/llvm-objdump','-d','--no-show-raw-insn','--no-leading-addr',p],capture_output=True,text=True).stdout
    d={};cur=None
    for l in out.splitlines():
        m=re.match(r'^<(.+)>:$',l.strip())
        if m and not m.group(1).startswith(("LBB",".L","LJTI")): cur=m.group(1); d[cur]=[]; continue
        if m: continue
        if cur and l.strip(): 
            s=l.strip(); s=re.sub(r' <[^>]*>','',s); s=re.sub(r'call -?0x[0-9a-f]+','call X',s); s=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',s)
            d[cur].append(s)
    return d
a,b=fns(sys.argv[1]),fns(sys.argv[2])
ch=[k for k in a if k in b and a[k]!=b[k]]
for k in ch: print(len(a[k])*8,len(b[k])*8,k)
print('changed',len(ch),'of',len(a))
