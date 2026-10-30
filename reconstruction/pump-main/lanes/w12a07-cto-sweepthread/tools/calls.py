#!/usr/bin/env python3
"""calls.py cand.so [cand_fn_start] : layout-order call sequence orig vs cand, with names; aligned."""
import sys,subprocess,re,difflib,os
B=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
ORIG='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w12a07-cto-sweepthread/reconstruction/base/original.so'
so=sys.argv[1]
syms={}
for l in subprocess.run([B+'/llvm-readelf','-sW','--demangle',so],capture_output=True,text=True).stdout.splitlines():
    p=l.split()
    if len(p)>7 and p[3]=='FUNC': syms[int(p[1],16)]=' '.join(p[7:])
def norm(n):
    n=re.sub(r'::h[0-9a-f]{16}$','',n); n=re.sub(r'\$[A-Za-z0-9]+\$','',n); n=re.sub(r'[^A-Za-z0-9_]','',n)
    return n[-40:]
def diso(path):
    t=subprocess.run([B+'/llvm-objdump','-dr','--demangle','--no-show-raw-insn','--section='+SEC,path],capture_output=True,text=True).stdout
    out=[];last=None
    for l in t.splitlines():
        m=re.match(r'\s*[0-9a-f]+:\s+R_SBF_64_(\d+)\s+(\S.*)',l)
        if m:
            if m.group(1)=='32' and out and out[-1][1].startswith('call'): out[-1][1]='callname '+norm(m.group(2))
            continue
        m=re.match(r'\s*(\d+):\s+(.*)',l)
        if m: out.append([int(m.group(1))*8,re.sub(r'\s*<.*>$','',m.group(2))]); continue
    return [tuple(x) for x in out]
def dis(path,s,n):
    out=[]
    t=subprocess.run([B+'/llvm-objdump','-d','--no-show-raw-insn','--start-address=%#x'%s,'--stop-address=%#x'%(s+n),path],capture_output=True,text=True).stdout
    for l in t.splitlines():
        m=re.match(r'\s*(\d+):\s+(.*)',l)
        if m: out.append((int(m.group(1))*8-s,re.sub(r'\s*<.*>$','',m.group(2))))
    return out
def seq(L,shift,base=0x22a10):
    r=[]
    for a,t in L:
        m=re.match(r'call (-?0x[0-9a-f]+)$',t)
        if m:
            x=int(m.group(1),16)
            x=(base+a+8+x*8)&0xffffffff
            if shift and x>=0x29518: x-=shift
            r.append((a,norm(syms.get(x,hex(x)))))
        elif t.startswith('callname'): r.append((a,t.split()[1]))
        elif t.startswith('syscall') or re.match(r'call -?\d+$',t): r.append((a,t))
    return r
for s,nm in syms.items():
    pass
cstart=0x22a10
if so.endswith('.o'):
    SEC=sys.argv[2]; syms={}
    for l in subprocess.run([B+'/llvm-readelf','-sW',ORIG.replace('original.so','original.so')],capture_output=True,text=True).stdout.splitlines(): pass
if so.endswith('.o'):
    CS=diso(so); csize=CS[-1][0]+8
else: csize=[int(p.split()[2]) for p in subprocess.run([B+'/llvm-readelf','-sW',so],capture_output=True,text=True).stdout.splitlines() if len(p.split())>7 and p.split()[1]=='%016x'%cstart and p.split()[3]=='FUNC'][0]
shift=27400-csize
if so.endswith('.o'):
    REF=sys.argv[3]
    for l in subprocess.run([B+'/llvm-readelf','-sW','--demangle',REF],capture_output=True,text=True).stdout.splitlines():
        p=l.split()
        if len(p)>7 and p[3]=='FUNC': syms[int(p[1],16)]=' '.join(p[7:])
    o=seq(dis(ORIG,0x22a10,27400),27400-int(sys.argv[4])); c=seq(CS,0)
else:
    o=seq(dis(ORIG,0x22a10,27400),shift); c=seq(dis(so,cstart,csize),0)
sm=difflib.SequenceMatcher(None,[x[1] for x in o],[x[1] for x in c],autojunk=False)
print('calls',len(o),len(c),'ratio',round(sm.ratio(),4))
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': print('= %d calls  orig %05x-%05x  cand %05x-%05x'%(i2-i1,o[i1][0],o[i2-1][0],c[j1][0],c[j2-1][0])); continue
    for k in range(max(i2-i1,j2-j1)):
        a=o[i1+k] if i1+k<i2 else None; b=c[j1+k] if j1+k<j2 else None
        print('%s %-70s | %s'%(tag[0], ('%05x %s'%a) if a else '', ('%05x %s'%b) if b else ''))
if os.environ.get('LIST'):
    print('--- orig'); [print('%05x %s'%x) for x in o]
    print('--- cand'); [print('%05x %s'%x) for x in c]
