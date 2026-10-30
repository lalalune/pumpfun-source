#!/usr/bin/env python3
"""mkblk.py <post.ll> <prefix> [n]: for every condbr X -> (A,B), swap the IR layout order of its successors
(move the later one just before the earlier one) = the layout effect of flipping the source if/match arm order."""
import sys,re,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import iredit
src,pre=sys.argv[1:3]; n=int(sys.argv[3]) if len(sys.argv)>3 else 6
mod=open(src).read(); _,fn,_=iredit.split_fn(mod); head,bl,tail=iredit.blocks(fn)
pos={lab:k for k,(lab,_) in enumerate(bl)}; items=[]
for lab,ls in bl:
    s=ls[iredit.term_index(ls)].strip()
    m=re.match(r'br i1 \S+, label %("[^"]+"|\S+), label %("[^"]+"|\S+?)(,|$)',s)
    if not m: continue
    a,b=m.group(1).strip('"'),m.group(2).strip('"')
    if a not in pos or b not in pos: continue
    if pos[a]<pos[b]: items.append(f'blk:{b}:{a}')
    else: items.append(f'blk:{a}:{b}')
    if pos[a]<pos[b]: items.append(f'blk:{a}:END')
    else: items.append(f'blk:{b}:END')
items=['{%s}'%i if ',' in i else i for i in items]
for k in range(n): open(f'{pre}_{k}.txt','w').write('\n'.join(items[k::n]))
print(len(items))
