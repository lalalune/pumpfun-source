#!/usr/bin/env python3
"""ann.py <unstripped.so> : main.dis with call target names"""
import sys,os,re,subprocess
M=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
so=sys.argv[1]
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
syms={}
for l in subprocess.run([SDK+'/llvm-readelf','-sW',so],capture_output=True,text=True).stdout.split('\n'):
    p=l.split()
    if len(p)>7 and p[3]=='FUNC': syms[int(p[1],16)]=p[7]
fs=[k for k,v in syms.items() if 'admin_cto7execute' in v][0]
for l in subprocess.run(['bash',M+'/tools/disso.sh',so],capture_output=True,text=True).stdout.split('\n'):
    m=re.match(r'(\w+)\s+call (-?0x\w+)',l)
    if m:
        off=int(m.group(1),16); imm=int(m.group(2),16)
        for t in [imm*8, fs+off+8+imm*8]:
            if t in syms:
                n=syms[t]; n=re.sub(r'17h[0-9a-f]{16}E$','',n); l+='   <'+n[-70:]+'>'; break
    print(l)
