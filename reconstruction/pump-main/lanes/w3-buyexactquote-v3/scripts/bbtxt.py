#!/usr/bin/env python3
"""bbtxt.py listing.txt : block map from normalized listing (fn.txt / orig-norm.txt)"""
import sys,re
L=[l.strip() for l in open(sys.argv[1]) if l.strip()]
addr=[];a=0
for l in L: addr.append(a); a+=16 if l.startswith('lddw') else 8
def tgt(i):
    m=re.search(r'([+-]0x[0-9a-f]+)$',L[i]); return addr[i]+8+int(m.group(1),16)*8
lead={0}
for i,l in enumerate(L):
    if l.startswith('j'): lead.add(tgt(i)); 
    if (l.startswith('j') or l=='exit') and i+1<len(L): lead.add(addr[i+1])
bid={x:k for k,x in enumerate(sorted(lead))}
out=[];cur=None
for i,l in enumerate(L):
    if addr[i] in bid: cur=[bid[addr[i]],addr[i],0,[]]; out.append(cur)
    cur[2]+=1
    if l.startswith('call'): cur[3].append('call')
    m=re.match(r'stw \[r10 - 0x[0-9a-f]+\], (0x3[0-9a-f]{2})$',l)
    if m: cur[3].append('L%d'%int(m.group(1),16))
    if l.startswith('j'): cur[3].append('%s->B%d'%(l.split()[0],bid.get(tgt(i),-1)))
    if l=='exit': cur[3].append('EXIT')
for b in out: print(f'B{b[0]:3d} {b[1]:5x} n={b[2]:3d} '+' '.join(b[3]))
