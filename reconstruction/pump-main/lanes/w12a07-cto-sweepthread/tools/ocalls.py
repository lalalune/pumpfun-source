#!/usr/bin/env python3
"""ocalls.py <orc-name> : call sequence of execute in the oracle object vs original (names normalized), aligned."""
import sys,subprocess,re,difflib,os
B=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w12a07-cto-sweepthread')
d=O+'/orc/'+sys.argv[1]
def norm(n):
    n=re.sub(r'::h[0-9a-f]{16}$','',n); n=re.sub(r'17h[0-9a-f]{16}E$','',n); n=re.sub(r'\$[A-Za-z0-9]+\$','',n); n=re.sub(r'[^A-Za-z0-9_]','',n)
    return n[-40:]
secs=subprocess.run([B+'/llvm-objdump','-h',d+'/m.o'],capture_output=True,text=True).stdout
sec=next(l.split()[1] for l in secs.splitlines() if 'admin_cto7execute17h' in l and '.rel' not in l)
t=subprocess.run([B+'/llvm-objdump','-dr','--no-show-raw-insn','--section='+sec,d+'/m.o'],capture_output=True,text=True).stdout
c=[];last=None
for l in t.splitlines():
    m=re.match(r'\s*[0-9a-f]+:\s+R_SBF_64_(\d+)\s+(\S.*)',l)
    if m:
        if c and c[-1][1]=='?': c[-1]=(c[-1][0],m.group(2).split('+')[0].strip())
        continue
    m=re.match(r'\s*(\d+):\s+(.*)',l)
    if m:
        ins=m.group(2)
        if ins.startswith('call') or ins.startswith('syscall'):
            c.append((int(m.group(1))*8,'?' if 'call' in ins else ins))
raw=[n for a,n in c]
dem=subprocess.run(['/usr/bin/c++filt'],input='\n'.join(raw),capture_output=True,text=True).stdout.splitlines()
c=[(a,('msg' if n=='?' or dm in ('sol_log_','abort') else norm(dm))) for (a,n),dm in zip(c,dem)]
o=[]
for l in open(O+'/an/calls_list.txt').read().split('--- cand')[0].splitlines()[1:]:
    a,n=l.split(None,1); o.append((int(a,16),n))
o=[(a,('msg' if n.startswith('0x') else n)) for a,n in o]
def nn(n): return n[-28:]
sm=difflib.SequenceMatcher(None,[nn(x[1]) for x in o],[nn(x[1]) for x in c],autojunk=False)
print('calls',len(o),len(c),'ratio',round(sm.ratio(),4))
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': print('= %d calls  orig %05x-%05x  cand %05x-%05x'%(i2-i1,o[i1][0],o[i2-1][0],c[j1][0],c[j2-1][0])); continue
    for k in range(max(i2-i1,j2-j1)):
        x=o[i1+k] if i1+k<i2 else None; y=c[j1+k] if j1+k<j2 else None
        print('%s %-50s | %s'%(tag[0], ('%05x %s'%x) if x else '', ('%05x %s'%y) if y else ''))
