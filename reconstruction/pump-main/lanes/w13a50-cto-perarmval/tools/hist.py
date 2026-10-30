#!/usr/bin/env python3
"""hist.py <m.o>..: instruction-class histogram, orig vs cands (class = opcode + operand kinds)."""
import sys,os,re,collections
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
def cls(t):
    op=t.split()[0]
    if 'r10 -' in t: return op+(' spill' if op.startswith('st') else ' reload') if re.search(r'r10 - 0x(8|9)[0-9a-f]{2}\]',t) else op+' frame'
    if op.startswith('ld') and '[' in t: return op+' mem'
    if op.startswith('st') and '[' in t: return op+' mem'
    if op=='mov64': return 'mov64 '+('imm' if re.search(r', -?(0x)?[0-9a-f]+$',t) else 'reg')
    if op.startswith('j'): return 'jmp'
    return op
o=collections.Counter(cls(t) for _,t in orig_dis())
C=[(p.split('/')[-2],collections.Counter(cls(t) for _,t in cand_dis(p))) for p in sys.argv[1:]]
keys=sorted(set(o)|set().union(*[set(c) for _,c in C]),key=lambda k:-o[k])
print('%-18s %6s'%('class','orig'),' '.join('%8s'%n for n,_ in C))
for k in keys:
    row=[c[k]-o[k] for _,c in C]
    if any(row): print('%-18s %6d'%(k,o[k]),' '.join('%+8d'%x for x in row))
