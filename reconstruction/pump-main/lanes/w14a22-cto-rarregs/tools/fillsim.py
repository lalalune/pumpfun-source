#!/usr/bin/env python3
# fillsim.py <orig_fn> <cand_fn> <nslots> [step] [lo] [hi]: insert nslots non-matching 8-B insns before cand insn k (scan k),
# fix every jump offset crossing the point, report scorer-style M and pinned ratio. Upper bound of a neutral fill at k.
import sys,re,difflib
from concurrent.futures import ProcessPoolExecutor
def rd(f):
    R=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        R.append((int(p[0],16),p[1].strip()))
    return R
def tok(s):
    s=re.sub(r'^call .*','call',s); return re.sub(r'lddw (r\d+), .*',r'lddw \1',s)
O=[tok(s) for _,s in rd(sys.argv[1])]; C=rd(sys.argv[2]); N=int(sys.argv[3])
def build(k):
    A=C[k][0] if k<len(C) else C[-1][0]+8
    out=[]
    for i,(a,s) in enumerate(C):
        if i==k: out+=[f'FILL{j}' for j in range(N)]
        m=re.match(r'^(j\w+.*?)([+-]0x[0-9a-f]+)$',s)
        if m and not s.startswith('call'):
            off=int(m.group(2),16); t=a+8+off*8
            na=a+(8*N if a>=A else 0); nt=t+(8*N if t>=A else 0)
            no=(nt-na-8)//8; s=m.group(1)+('+' if no>=0 else '-')+hex(abs(no))
        out.append(tok(s))
    return out
def M(c): return sum(b.size for b in difflib.SequenceMatcher(None,O,c,autojunk=False).get_matching_blocks())
def job(k):
    c=build(k); m=M(c); return k,C[k][0] if k<len(C) else -1,m,2*m/(len(O)+len(c))
if __name__=='__main__':
    st=int(sys.argv[4]) if len(sys.argv)>4 else 16; lo=int(sys.argv[5]) if len(sys.argv)>5 else 0; hi=int(sys.argv[6]) if len(sys.argv)>6 else len(C)
    print('base M',M([tok(s) for _,s in C]),flush=True)
    with ProcessPoolExecutor(4) as ex:
        for k,a,m,r in ex.map(job,range(lo,hi,st)): print(k,hex(a),m,f'{r:.5f}',flush=True)
