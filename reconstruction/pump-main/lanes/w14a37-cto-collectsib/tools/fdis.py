#!/usr/bin/env python3
"""fdis.py <so> <addr> <size> : fn-relative disasm with call names (base symbols)."""
import sys,subprocess,re,os
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/')
B=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
so,st,sz=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3])
syms={}
for l in subprocess.run([SDK+'llvm-readelf','-sW',B],capture_output=True,text=True).stdout.split('\n'):
    p=l.split()
    if len(p)>=8 and p[3]=='FUNC': syms[int(p[1],16)]=p[7]
def dm(n):
    s=n[3:] if n.startswith('_ZN') else n; i=0; parts=[]
    while i<len(s) and s[i].isdigit():
        j=i
        while s[j].isdigit(): j+=1
        k=int(s[i:j]); parts.append(s[j:j+k]); i=j+k
    parts=[p for p in parts if not re.fullmatch(r'h[0-9a-f]{16}',p)]
    return ('::'.join(parts[-2:]) or n).replace('$LT$','<').replace('$GT$','>').replace('$u20$',' ')
d=subprocess.run([SDK+'llvm-objdump','-d','--no-show-raw-insn','--start-address=%d'%st,'--stop-address=%d'%(st+sz),so],capture_output=True,text=True).stdout
for l in d.split('\n'):
    m=re.match(r'\s*(\d+):\s+(.*)',l)
    if not m: continue
    a=int(m.group(1))*8; s=re.sub(r'\s*<[^>]*>','',m.group(2).strip())
    mm=re.match(r'call (-?0x[0-9a-f]+)$',s)
    if mm:
        t=a+8+int(mm.group(1),16)*8; s+='   <'+dm(syms.get(t,'?%x'%t))+'>'
    print('%04x %s'%(a-st,s))
