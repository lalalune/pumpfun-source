#!/usr/bin/env python3
"""ann.py <rel.dis> [lo hi] : annotate call targets (function-relative disasm, fn at 0x22a10) with base symbol names."""
import sys,subprocess,re,os,bisect
B=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
RE=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llvm-readelf')
syms={}
for l in subprocess.run([RE,'-sW',B],capture_output=True,text=True).stdout.split('\n'):
    p=l.split()
    if len(p)>=8 and p[3]=='FUNC': syms[int(p[1],16)]=p[7]
def dm(n):
    m=re.findall(r'(\d+)([A-Za-z_$][\w$.]*)',n)
    out=[];s=n[3:] if n.startswith('_ZN') else n
    i=0;parts=[]
    while i<len(s) and s[i].isdigit():
        j=i
        while s[j].isdigit(): j+=1
        k=int(s[i:j]); parts.append(s[j:j+k]); i=j+k
    parts=[p for p in parts if not re.fullmatch(r'h[0-9a-f]{16}',p)]
    return '::'.join(parts[-2:]).replace('$LT$','<').replace('$GT$','>').replace('$u20$',' ')
lo,hi=(int(sys.argv[2],16),int(sys.argv[3],16)) if len(sys.argv)>3 else (0,1<<30)
for l in open(sys.argv[1]):
    q=l.split(None,1); a=int(q[0],16)
    if not lo<=a<hi: continue
    s=q[1].rstrip(); m=re.match(r'call (-?0x[0-9a-f]+)$',s)
    if m:
        t=0x22a10+a+8+int(m.group(1),16)*8
        s+='   <'+dm(syms.get(t,'?%x'%t))+'>'
    print('%04x %s'%(a,s))
