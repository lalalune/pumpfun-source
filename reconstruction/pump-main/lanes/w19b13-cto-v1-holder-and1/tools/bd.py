#!/usr/bin/env python3
# bd.py <a.bin|name> <b.bin|name> [--mask rfj]: masked diff of two fn bins: prints opcode runs that differ, with window offsets, disassembled
import sys,os,difflib,re
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w19b13-cto-v1-holder-and1')
sys.path.insert(0,OUT+'/tools')
import dis as D
W=D.W
def L(n):
    p=f'{OUT}/fx/{n}/fn.bin' if not n.endswith('.bin') else n
    if n=='orig':
        import oracle
        return list(D.dis(oracle.orig_window()))
    return list(D.dis(open(p,'rb').read()))
def ab(t):
    # abstract registers, frame offsets, jump offsets
    t=re.sub(r'\br\d+\b','R',t) if 'r' in MASK else t
    if 'f' in MASK: t=re.sub(r'\[r10 - 0x[0-9a-f]+\]','[FP]',t); t=re.sub(r'\[R - 0x[0-9a-f]+\]','[FP]',t)
    if 'j' in MASK:
        if t.startswith('j'): t=re.sub(r'[-+]0x[0-9a-f]+$','J',t)
    if t.startswith('call'): t='call'
    if t.startswith('lddw'): t=t.split(',')[0]
    return t
a=sys.argv[1]; b=sys.argv[2]; MASK=sys.argv[sys.argv.index('--mask')+1] if '--mask' in sys.argv else 'rfj'
A=L(a); B=L(b)
aa=[ab(t) for _,t in A]; bb=[ab(t) for _,t in B]
sm=difflib.SequenceMatcher(None,aa,bb,autojunk=False)
print('M(mask=%s)'%MASK,sum(x.size for x in sm.get_matching_blocks()),'len',len(aa),len(bb))
lim=int(sys.argv[sys.argv.index('--lim')+1]) if '--lim' in sys.argv else 40
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    print(f'--- {tag} a[{A[i1][0]-W if i1<len(A) else -1:#x}..] {i2-i1} b[{B[j1][0]-W if j1<len(B) else -1:#x}..] {j2-j1}')
    for k in range(i1,min(i2,i1+lim)): print(f'   - {A[k][0]-W:#06x} {A[k][1]}')
    for k in range(j1,min(j2,j1+lim)): print(f'   + {B[k][0]-W:#06x} {B[k][1]}')
