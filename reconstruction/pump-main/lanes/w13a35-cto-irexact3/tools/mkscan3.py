#!/usr/bin/env python3
"""mkscan3.py <post.ll> <prefix> [nproc]: non-alloca-move single edits: bw 1:2000, 2000:1, 20:12 and inv on every condbr,
sz:A:+-8 on every alloca, swapphi on every block with >=1 phi (2+ incoming). Writes <prefix>_k.txt."""
import sys,re,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import iredit
src,pre=sys.argv[1:3]; n=int(sys.argv[3]) if len(sys.argv)>3 else 8
mod=open(src).read(); _,fn,_=iredit.split_fn(mod)
head,bl,tail=iredit.blocks(fn)
items=[]
for lab,ls in bl:
    s=ls[iredit.term_index(ls)].strip()
    if s.startswith('br i1'):
        items+=[f'bw:{lab}:1:2000',f'bw:{lab}:2000:1',f'bw:{lab}:20:12',f'inv:{lab}']
for m in re.finditer(r'^\s*%(\S+) = alloca \[(\d+) x i8\]',fn,re.M):
    a,sz=m.group(1),int(m.group(2))
    for d in (-8,8):
        if sz+d>0: items.append(f'sz:{a}:{sz+d}')
for lab,ls in bl:
    if any(re.match(r'^\s*%[-\w.$"]+ = phi .*\],\s*\[',l) for l in ls):
        items.append(f'swapphi:{lab}')
items=['{%s}'%i if ',' in i else i for i in items]
for k in range(n): open(f'{pre}_{k}.txt','w').write('\n'.join(items[k::n]))
print(len(items))
