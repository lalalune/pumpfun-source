#!/usr/bin/env python3
"""rdiff.py A B [lo hi]: opcode-skeleton diff (regs/frame/imm masked) of two fn blobs (main|orig|rx name), list of non-equal ranges."""
import sys,difflib,re,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import sbpfdis as D, oracle
def blob(n):
    if n=='orig': return oracle.orig_window()
    if n=='main': return oracle.elf_fn(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so'),oracle.KEEP)
    return open(n if os.path.exists(n) else T+'/../rx/'+n+'/fn.bin','rb').read()
def sk(s): return re.sub(r'r\d+','r',re.sub(r'0x[0-9a-f]+|-?\d+','N',s))
a,b=sys.argv[1:3]; A=D.d(blob(a)); B=D.d(blob(b))
lo=int(sys.argv[3],16) if len(sys.argv)>3 else 0; hi=int(sys.argv[4],16) if len(sys.argv)>4 else 1<<30
sm=difflib.SequenceMatcher(None,[sk(x[1]) for x in A],[sk(x[1]) for x in B],autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    if not (lo<=A[min(i1,len(A)-1)][0]<=hi): continue
    print(f'{tag:8s} {a}[{A[i1][0] if i1<len(A) else -1:#x}..{A[i2-1][0] if i2>i1 else -1:#x}] n={i2-i1}  {b}[{B[j1][0] if j1<len(B) else -1:#x}..{B[j2-1][0] if j2>j1 else -1:#x}] n={j2-j1}')
