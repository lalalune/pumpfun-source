#!/usr/bin/env python3
"""calls.py <unstripped.so> <dis> [lo hi]: annotate execute's calls with callee symbols."""
import sys,subprocess,re,os,bisect
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/')
so=sys.argv[1]; dis=sys.argv[2]; lo=int(sys.argv[3],16) if len(sys.argv)>3 else 0; hi=int(sys.argv[4],16) if len(sys.argv)>4 else 1<<30
t=subprocess.run([SDK+'llvm-objdump','-t','-C',so],capture_output=True,text=True).stdout
syms=[]
for l in t.split('\n'):
    m=re.match(r'([0-9a-f]{16}) .{7} (\S+)\s+([0-9a-f]{16}) (.*)',l)
    if m and m.group(2).startswith('.text'): syms.append((int(m.group(1),16),m.group(4)))
syms.sort(); addrs=[a for a,_ in syms]
st=[a for a,n in syms if 'admin_cto::execute' in n][0]
for l in open(dis):
    a=int(l[:4],16)
    if not(lo<=a<hi): continue
    m=re.match(r'[0-9a-f]+ call (-?0x[0-9a-f]+)',l)
    if m:
        imm=int(m.group(1),16)
        if imm==-1: print('%04x call SYSCALL/reloc'%a); continue
        tgt=st+a+8+imm*8; i=bisect.bisect_right(addrs,tgt)-1
        print('%04x call %s%s'%(a,syms[i][1][:110],'' if syms[i][0]==tgt else '+%x'%(tgt-syms[i][0])))
