#!/usr/bin/env python3
"""slots.py <m.o> [lo hi]: per 8B frame slot in [lo,hi], list accesses in orig and candidate (offset:op) side by side."""
import sys,re,subprocess,os,collections
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
ORIG=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w13a20-cto-unmerged24/orig.dis')
def cand_dis(p):
    if p.endswith('.so'):
        nm=subprocess.run([SDK+'/llvm-objdump','-t',p],capture_output=True,text=True).stdout
        ln=[l for l in nm.splitlines() if 'admin_cto7execute' in l][0].split()
        st=int(ln[0],16); sz=int(ln[4],16)
        raw=subprocess.run([SDK+'/llvm-objdump','-d','--no-show-raw-insn','--start-address=%d'%st,'--stop-address=%d'%(st+sz),p],capture_output=True,text=True).stdout
        L=[(int(m.group(1)),re.sub(r'\s+<[^>]*>','',m.group(2)).strip()) for m in (re.match(r'^\s*(\d+):\s+(.*)$',l) for l in raw.splitlines()) if m]
        b=L[0][0]; return [((i-b)*8,t) for i,t in L]
    h=subprocess.run([SDK+'/llvm-objdump','-h',p],capture_output=True,text=True).stdout
    sec=re.search(r'(\.text\.\S*admin_cto7execute\S*)',h).group(1)
    raw=subprocess.run([SDK+'/llvm-objdump','-d','--no-show-raw-insn',p,'--section='+sec],capture_output=True,text=True).stdout
    return [(int(m.group(1))*8,re.sub(r'\s+<[^>]*>','',m.group(2)).strip()) for m in (re.match(r'^\s*(\d+):\s+(.*)$',l) for l in raw.splitlines()) if m]
def orig_dis():
    r=[]
    for l in open(ORIG):
        m=re.match(r'^(0x[0-9a-f]+)\s+(.*)$',l)
        if m: r.append((int(m.group(1),16)-0x22a10,re.sub(r'\s+<[^>]*>','',m.group(2)).strip()))
    return r
def acc(d):
    s=collections.defaultdict(list)
    for o,t in d:
        m=re.search(r'r10 - 0x([0-9a-f]+)',t)
        if m:
            k=int(m.group(1),16)
            kind='S' if t.startswith('st') else 'L'
            reg=re.search(r'\b(r\d)\b',t.replace('r10','')).group(1) if re.search(r'\b(r\d)\b',t.replace('r10','')) else 'imm'
            s[k].append('%s%x%s'%(kind,o,'' if kind=='L' else '') )
    return s
if __name__=='__main__':
    p=sys.argv[1]; lo=int(sys.argv[2],16) if len(sys.argv)>2 else 0x8d0; hi=int(sys.argv[3],16) if len(sys.argv)>3 else 0xc40
    a=acc(orig_dis()); b=acc(cand_dis(p))
    for k in range(lo,hi+1,8):
        print('%4x | o %-60s | c %s'%(k,' '.join(a.get(k,[]))[:60],' '.join(b.get(k,[]))[:60]))
